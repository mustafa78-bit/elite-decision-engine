# core/process/scheduler.py
"""Scheduler engine implementing Process state progression, interrupts, resume, and limits."""
from __future__ import annotations

import logging
import queue
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Set

from core.process.model import CognitiveProcess, ProcessState
from core.process.working_memory import WorkingMemory
from core.process.process_table import ChannelScopedProcessTable
from core.process.resource_manifest import ResourceManifest
from core.process.atomic import YieldPoint, AtomicDurationExceeded
from core.process.checkpoints import CheckpointRegistry, ProcessCheckpoint
from core.process.interrupts import LocalInterrupt, InterruptSeverity
from core.process.telemetry import TelemetryService
from core.process.events import ProcessEventLogger
from core.process.versioning import VersionedState, ConcurrentUpdateError

logger = logging.getLogger(__name__)


class Scheduler:
    """Core process scheduler orchestrating process lifecycles and constraints."""

    def __init__(
        self,
        event_logger: Optional[ProcessEventLogger] = None,
        telemetry: Optional[TelemetryService] = None,
    ) -> None:
        self.process_table = ChannelScopedProcessTable()
        self.checkpoints = CheckpointRegistry()
        self.telemetry = telemetry or TelemetryService()
        self.event_logger = event_logger or ProcessEventLogger()

        # Shared priority queue tracking processes to run
        # Priority queue in python processes lowest values first, so we invert priority value to run highest first
        # Element format: (priority, counter, timestamp, process) to prevent TypeError on identical priorities
        self._queue: queue.PriorityQueue[Tuple[int, int, float, CognitiveProcess]] = queue.PriorityQueue()
        self._counter: int = 0  # Monotonically increasing counter to prevent CognitiveProcess comparison TypeErrors
        self._queued_ids: Set[str] = set()  # Track currently queued process IDs to prevent duplicate queueing

        # Process ID mapping to isolated WorkingMemory instances
        self.memories: Dict[str, WorkingMemory] = {}

        # Local Real-Time Interrupt path queue
        self._interrupt_queue: List[LocalInterrupt] = []

        # Scheduler configuration
        self.degraded_mode: bool = False
        self.atomic_limit_sec: float = 0.5  # default max continuous slice
        self.starvation_threshold_sec: float = 1.0  # Time queued before a priority bump is triggered

    def enable_degraded_mode(self, enabled: bool = True) -> None:
        """Toggle degraded scheduling mode (bypasses non-critical processes)."""
        self.degraded_mode = enabled
        logger.warning("[SCHEDULER] Degraded mode set to %s", enabled)

    def register_and_queue_process(
        self,
        process: CognitiveProcess,
        manifest: Optional[ResourceManifest] = None,
    ) -> None:
        """Register process in table, initialize its working memory, and place into the queue."""
        self.process_table.register_process(process)
        if process.id not in self.memories:
            self.memories[process.id] = WorkingMemory(process.id)

        # Prevent duplicate queueing of the same process instance
        if process.id in self._queued_ids:
            logger.debug("Process %s is already queued, skipping duplicate queueing", process.id)
            return

        self.telemetry.metrics.processes_queued += 1
        self._queued_ids.add(process.id)

        # Resource limit verification (ceiling priority constraints)
        effective_priority = process.priority
        if manifest:
            if effective_priority > manifest.ceiling_priority:
                effective_priority = manifest.ceiling_priority
                logger.info(
                    "Priority clamped to ceiling %s for process %s",
                    manifest.ceiling_priority, process.id
                )

        # Invert priority so higher priority numbers are processed first
        # Use counter as secondary tie breaker to guarantee FIFO ordering within identical priorities and prevent CognitiveProcess comparison
        self._counter += 1
        self._queue.put((-effective_priority, self._counter, time.time(), process))
        self.event_logger.record_process_event(
            event_type="Process Registered",
            process_id=process.id,
            description=f"Process '{process.name}' queued successfully with priority {effective_priority}",
            details={"channel": process.channel, "priority": effective_priority},
        )

    def trigger_local_interrupt(self, interrupt: LocalInterrupt) -> None:
        """Inject a real-time pre-emptive interrupt into the scheduler flow."""
        self._interrupt_queue.append(interrupt)
        self.telemetry.record_interrupt()
        self.event_logger.record_process_event(
            event_type="Interrupt Triggered",
            process_id=interrupt.target_process_id,
            description="Scheduler received pre-emptive local interrupt",
            details={"interrupt_id": interrupt.id, "severity": interrupt.severity.value},
        )

    def _apply_anti_starvation(self) -> None:
        """Perform an anti-starvation pass over queued processes, bumping priority if they wait too long."""
        if self._queue.empty():
            return

        now = time.time()
        temp_list = []
        starvation_occurred = False

        # Drain queue
        while not self._queue.empty():
            temp_list.append(self._queue.get())

        # Check and rebuild queue
        for priority_val, count, timestamp, process in temp_list:
            elapsed = now - timestamp
            if elapsed > self.starvation_threshold_sec:
                # Priority value is inverted negative, so to increase/bump priority we subtract (make more negative)
                new_priority_val = priority_val - 20  # Bump priority by 20 points
                starvation_occurred = True
                logger.info(
                    "[SCHEDULER] Anti-starvation triggered for process %s. Priority bumped from %s to %s.",
                    process.id, -priority_val, -new_priority_val
                )
                self.event_logger.record_process_event(
                    event_type="Anti-Starvation Triggered",
                    process_id=process.id,
                    description=f"Process priority bumped dynamically to prevent starvation",
                    details={"old_priority": -priority_val, "new_priority": -new_priority_val},
                )
                self._queue.put((new_priority_val, count, timestamp, process))
            else:
                self._queue.put((priority_val, count, timestamp, process))

    def process_next(self) -> Optional[Any]:
        """Execute the next available cognitive process within all limits and checks."""
        if self._queue.empty():
            return None

        # Run anti-starvation check
        self._apply_anti_starvation()

        # Handle pre-emptive local interrupts first
        if self._interrupt_queue:
            active_interrupts = [i for i in self._interrupt_queue if not i.handled]
            for interrupt in active_interrupts:
                # Flag interrupt handled and record to event ledger
                interrupt.handled = True
                self.event_logger.record_process_event(
                    event_type="Interrupt Handled",
                    process_id=interrupt.target_process_id,
                    description=f"Pre-emptive interrupt {interrupt.id} processed",
                    details={"payload": interrupt.payload, "severity": interrupt.severity.value},
                )
                # Lookup process across all channels if not found in default
                target_proc = self.process_table.get_process(interrupt.target_process_id)
                if target_proc:
                    target_proc.priority = 100  # Ceiling/Interrupt priority
                    self.register_and_queue_process(target_proc)

        priority_val, _, _, process = self._queue.get()
        if process.id in self._queued_ids:
            self._queued_ids.remove(process.id)

        # Degraded Scheduler Mode checks
        if self.degraded_mode and process.priority < 80:
            logger.warning("[SCHEDULER] Skipping process %s because scheduler is in Degraded Mode", process.id)
            process.state = ProcessState.BLOCKED
            self.telemetry.record_failed()
            return None

        # Build execution environment and enforce yield point checks
        yield_point = YieldPoint(self.atomic_limit_sec)
        process.state = ProcessState.RUNNING
        process.yield_point = yield_point

        try:
            # Yield-point check before starting execution
            yield_point.check_and_enforce()

            # Execute
            result = process.run()

            # Handle commit-or-retry semantics if process returns state change tuple
            # If function returned Tuple[VersionedState, Any, int], apply optimistic concurrency check
            if isinstance(result, tuple) and len(result) == 3 and isinstance(result[0], VersionedState):
                v_state, mutated_val, expected_version = result
                try:
                    v_state.mutate(mutated_val, expected_version)
                    self.event_logger.record_process_event(
                        event_type="State Committed",
                        process_id=process.id,
                        description="Optimistic state update committed successfully",
                        details={"version": v_state.version},
                    )
                except ConcurrentUpdateError as concurrency_err:
                    self.telemetry.metrics.retry_attempts += 1
                    logger.warning("State commit failed: %s. Requeuing process for retry.", concurrency_err)
                    self.event_logger.record_process_event(
                        event_type="Commit Retried",
                        process_id=process.id,
                        description="State commit failed due to concurrency conflict, retrying process",
                        details={"error": str(concurrency_err)},
                    )
                    process.version += 1  # progress process tracking version
                    self.register_and_queue_process(process)
                    return None

            process.state = ProcessState.COMPLETED
            self.telemetry.record_completed()
            self.event_logger.record_process_event(
                event_type="Process Completed",
                process_id=process.id,
                description=f"Process '{process.name}' completed execution",
                details={"execution_count": process.execution_count},
            )
            return result

        except AtomicDurationExceeded as ade:
            self.telemetry.record_yield()
            self.telemetry.record_guarantee_violation(process.id, str(ade))
            process.state = ProcessState.YIELDED
            self.event_logger.record_process_event(
                event_type="Process Yielded",
                process_id=process.id,
                description=f"Process yielded: {ade}",
                details={"execution_count": process.execution_count},
            )
            # Requeue yielded process to execute in next scheduler iteration
            self._counter += 1
            self._queued_ids.add(process.id)
            self._queue.put((priority_val, self._counter, time.time(), process))
            return None

        except Exception as e:
            process.state = ProcessState.FAILED
            process.error = str(e)
            self.telemetry.record_failed()
            self.event_logger.record_process_event(
                event_type="Process Failed",
                process_id=process.id,
                description=f"Process execution failed: {e}",
                details={"error": str(e)},
            )
            raise e
        finally:
            process.yield_point = None

    def resume_process_from_checkpoint(
        self,
        process: CognitiveProcess,
        checkpoint_id: str,
        expected_version: int,
    ) -> bool:
        """Resume process with state snapshot if version validation passes."""
        checkpoint = self.checkpoints.get_checkpoint(process.id, checkpoint_id)
        if not checkpoint:
            logger.error("Checkpoint %s not found for process %s", checkpoint_id, process.id)
            return False

        # Version validation check
        if checkpoint.version != expected_version:
            logger.error(
                "Version validation failed for process %s resume. Checkpoint version: %s, Expected: %s",
                process.id, checkpoint.version, expected_version
            )
            self.telemetry.record_guarantee_violation(
                process.id, f"Resume version mismatch: Checkpoint {checkpoint.version} vs Expected {expected_version}"
            )
            return False

        # Apply snapshot restore to isolated working memory
        working_mem = self.memories.get(process.id)
        if not working_mem:
            working_mem = WorkingMemory(process.id)
            self.memories[process.id] = working_mem

        working_mem.clear()
        for k, v in checkpoint.memory_snapshot.items():
            working_mem.set(k, v)

        process.state = ProcessState.PENDING
        self.register_and_queue_process(process)
        self.event_logger.record_process_event(
            event_type="Process Resumed",
            process_id=process.id,
            description=f"Process resumed from checkpoint '{checkpoint_id}' with version verification",
            details={"checkpoint_version": checkpoint.version, "milestone": checkpoint.milestone_name},
        )
        return True

    def run_all_simulated(self) -> None:
        """Simulate distributed execution model of queued processes."""
        while not self._queue.empty():
            self.process_next()
