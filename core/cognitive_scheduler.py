from __future__ import annotations

import logging
from dataclasses import dataclass, field
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class VersionValidationError(Exception):
    """Raised when an optimistic concurrency version check fails."""
    pass


class SchedulingGuaranteeViolation(Exception):
    """Raised when a core scheduler guarantee is violated (e.g. timeout, drift, degraded limits)."""
    pass


@dataclass
class ResourceManifest:
    """Defines CPU, memory, and duration boundaries for a Cognitive Process."""
    default_cpu_share: float = 1.0  # Normalized CPU units [0.0 - 1.0]
    ceiling_cpu_share: float = 1.0
    max_duration_seconds: float = 10.0  # Duration deadline
    max_memory_mb: float = 512.0


@dataclass
class CognitiveProcess:
    """Represents a scheduled unit of cognitive work in the NEXUS Decision OS."""
    process_id: str
    name: str
    owner: str
    priority: int = 10  # Lower number = higher priority
    state: str = "PENDING"  # PENDING, RUNNING, SUSPENDED, COMPLETED, FAILED
    version: int = 1
    working_memory: Dict[str, Any] = field(default_factory=dict)
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)
    manifest: ResourceManifest = field(default_factory=ResourceManifest)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actual_duration: float = 0.0
    actual_memory_mb: float = 0.0

    def increment_version(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def checkpoint(self, data: Dict[str, Any]) -> None:
        """Saves current state and progress for checkpointing/resume."""
        self.checkpoint_data = data
        self.increment_version()

    def update_memory(self, memory_slice: Dict[str, Any], expected_version: int) -> None:
        """Optimistic concurrency protected working memory update."""
        if self.version != expected_version:
            raise VersionValidationError(
                f"Version mismatch for process {self.process_id}: "
                f"expected {expected_version}, actual {self.version}"
            )
        self.working_memory.update(memory_slice)
        self.increment_version()


class SharedVersionedQueue:
    """Thread-safe, versioned queue of cognitive processes waiting to be scheduled."""

    def __init__(self) -> None:
        self.version: int = 1
        self._queue: List[CognitiveProcess] = []
        self._lock = threading.Lock()

    def enqueue(self, process: CognitiveProcess, expected_version: int) -> None:
        """Atomic, version-validated enqueue operation."""
        with self._lock:
            if self.version != expected_version:
                raise VersionValidationError(
                    f"Queue version conflict: expected {expected_version}, actual {self.version}"
                )
            self._queue.append(process)
            self.version += 1

    def dequeue(self, expected_version: int) -> Optional[CognitiveProcess]:
        """Atomic, version-validated dequeue operation with priority-aging (anti-starvation)."""
        with self._lock:
            if self.version != expected_version:
                raise VersionValidationError(
                    f"Queue version conflict: expected {expected_version}, actual {self.version}"
                )
            if not self._queue:
                return None
            # Age pending processes to prevent starvation
            for p in self._queue:
                if p.priority > 1:
                    p.priority -= 1
            # Dequeue based on priority (lower priority number first)
            self._queue.sort(key=lambda p: p.priority)
            proc = self._queue.pop(0)
            self.version += 1
            return proc

    def commit_or_retry(self, action_func: Callable[[List[CognitiveProcess]], tuple[Any, List[CognitiveProcess]]], max_retries: int = 5) -> Any:
        """Executes action_func with optimistic commit-or-retry logic."""
        for attempt in range(max_retries):
            current_version = self.version
            try:
                # Local copy/simulation of queue state for processing
                with self._lock:
                    copied_queue = list(self._queue)

                # Run the transaction function
                res, updated_queue = action_func(copied_queue)

                with self._lock:
                    if self.version != current_version:
                        # Version changed during execution, retry!
                        continue
                    self._queue = updated_queue
                    self.version += 1
                    return res
            except VersionValidationError:
                if attempt == max_retries - 1:
                    raise
                continue
        raise VersionValidationError("Transaction failed after maximum commit-or-retry attempts.")


class ChannelScopedProcessTable:
    """Thread-safe workstation/channel scoped mapping of active CognitiveProcesses."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # channel_id -> process_id -> CognitiveProcess
        self._table: Dict[str, Dict[str, CognitiveProcess]] = defaultdict(dict)

    def register(self, channel_id: str, process: CognitiveProcess) -> None:
        with self._lock:
            self._table[channel_id][process.process_id] = process

    def unregister(self, channel_id: str, process_id: str) -> Optional[CognitiveProcess]:
        with self._lock:
            return self._table[channel_id].pop(process_id, None)

    def get_process(self, channel_id: str, process_id: str) -> Optional[CognitiveProcess]:
        with self._lock:
            return self._table[channel_id].get(process_id)

    def get_active_processes(self, channel_id: str) -> List[CognitiveProcess]:
        with self._lock:
            return list(self._table[channel_id].values())

    def get_all_active_processes(self) -> Dict[str, List[CognitiveProcess]]:
        with self._lock:
            return {chan: list(procs.values()) for chan, procs in self._table.items()}


class CognitiveScheduler:
    """Core cognitive scheduler orchestrating execution of CognitiveProcesses in NEXUS."""

    def __init__(self, queue: Optional[SharedVersionedQueue] = None) -> None:
        self.queue = queue or SharedVersionedQueue()
        self.process_table = ChannelScopedProcessTable()
        self.degraded_mode: bool = False
        self.drift_alerts: List[Dict[str, Any]] = []
        self.violations_log: List[Dict[str, Any]] = []
        self._current_running_process: Optional[CognitiveProcess] = None
        self._lock = threading.Lock()

    def enqueue_process(self, channel_id: str, process: CognitiveProcess) -> None:
        """Enqueues and registers a new cognitive process."""
        self.process_table.register(channel_id, process)
        process.state = "PENDING"
        self.queue.enqueue(process, expected_version=self.queue.version)

    def interrupt_process(self, channel_id: str, process_id: str) -> None:
        """Local Real-Time Interrupt path to immediately preempt a process."""
        with self._lock:
            process = self.process_table.get_process(channel_id, process_id)
            if not process:
                return
            if process.state == "RUNNING":
                # Pause and checkpoint
                process.checkpoint({"paused_at": datetime.now(timezone.utc).isoformat()})
                process.state = "SUSPENDED"
                self.violations_log.append({
                    "event": "INTERRUPT",
                    "process_id": process_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": "Real-time interrupt triggered preemption."
                })
                if self._current_running_process and self._current_running_process.process_id == process_id:
                    self._current_running_process = None

    def resume_process(self, channel_id: str, process_id: str) -> None:
        """Resumes a suspended process from its checkpoint."""
        with self._lock:
            process = self.process_table.get_process(channel_id, process_id)
            if not process:
                return
            if process.state == "SUSPENDED":
                process.state = "PENDING"
                process.increment_version()
                self.queue.enqueue(process, expected_version=self.queue.version)

    def yield_point(self, process: CognitiveProcess) -> bool:
        """Yield point checking. Returns True if preemption was handled."""
        with self._lock:
            if process.state == "SUSPENDED":
                # Preemption was handled gracefully
                return True
            return False

    def enter_degraded_mode(self) -> None:
        """Enenters degraded mode, adjusting ceiling resource limits."""
        self.degraded_mode = True
        logger.warning("Cognitive Scheduler entered degraded mode. Stricter constraints active.")

    def exit_degraded_mode(self) -> None:
        self.degraded_mode = False

    def execute_step(self, channel_id: str) -> Optional[CognitiveProcess]:
        """Runs a single scheduler execution slice."""
        with self._lock:
            # 1. Resolve and dequeue next process
            try:
                proc = self.queue.dequeue(expected_version=self.queue.version)
            except VersionValidationError:
                # Retrying queue dequeue
                proc = self.queue.dequeue(expected_version=self.queue.version)

            if not proc:
                return None

            # Check if degraded mode forces drop of low priority processes
            if self.degraded_mode and proc.priority > 5:
                proc.state = "FAILED"
                self.violations_log.append({
                    "event": "TASK_DROPPED",
                    "process_id": proc.process_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": "Process dropped under scheduler degraded mode."
                })
                raise SchedulingGuaranteeViolation(
                    f"Process {proc.process_id} dropped: low priority under degraded mode."
                )

            # 2. Run/Resume process
            proc.state = "RUNNING"
            proc.increment_version()
            self._current_running_process = proc

            # Simulate duration increment and memory consumption
            proc.actual_duration += 1.0
            proc.actual_memory_mb += 128.0

            # 3. Resource Manifest boundaries check & Drift Detection
            manifest = proc.manifest
            if proc.actual_memory_mb > manifest.max_memory_mb:
                alert = {
                    "process_id": proc.process_id,
                    "metric": "memory",
                    "actual": proc.actual_memory_mb,
                    "limit": manifest.max_memory_mb,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                self.drift_alerts.append(alert)
                # Auto-trigger degraded mode on memory breach
                self.enter_degraded_mode()

            # 4. Atomic duration limit enforcement
            if proc.actual_duration > manifest.max_duration_seconds:
                proc.state = "FAILED"
                self._current_running_process = None
                self.violations_log.append({
                    "event": "DURATION_VIOLATION",
                    "process_id": proc.process_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": f"Duration {proc.actual_duration}s exceeded max {manifest.max_duration_seconds}s"
                })
                raise SchedulingGuaranteeViolation(
                    f"Process {proc.process_id} violated atomic duration guarantee: "
                    f"actual {proc.actual_duration}s vs max {manifest.max_duration_seconds}s"
                )

            # Completes successfully if within limits
            proc.state = "COMPLETED"
            proc.increment_version()
            self._current_running_process = None
            return proc

    def get_observability_metrics(self) -> Dict[str, Any]:
        """Exposes observability diagnostic statistics for the scheduler."""
        active_by_channel = self.process_table.get_all_active_processes()
        return {
            "queue_version": self.queue.version,
            "queue_size": len(self.queue._queue),
            "degraded_mode": self.degraded_mode,
            "drift_alerts_count": len(self.drift_alerts),
            "drift_alerts": self.drift_alerts,
            "violations": self.violations_log,
            "active_processes_count": sum(len(procs) for procs in active_by_channel.values()),
            "channels": {chan: [p.process_id for p in procs] for chan, procs in active_by_channel.items()}
        }
