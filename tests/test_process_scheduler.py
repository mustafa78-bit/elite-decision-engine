# tests/test_process_scheduler.py
"""Comprehensive isolated unit and integration tests verifying Sprint XII v2 Process Scheduler."""
from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from core.process.model import CognitiveProcess, ProcessState
from core.process.working_memory import WorkingMemory
from core.process.resource_manifest import ResourceManifest
from core.process.atomic import YieldPoint, AtomicDurationExceeded
from core.process.checkpoints import CheckpointRegistry
from core.process.interrupts import LocalInterrupt, InterruptSeverity
from core.process.versioning import VersionedState, ConcurrentUpdateError
from core.process.scheduler import Scheduler
from core.process.telemetry import TelemetryService


def test_cognitive_process_initial_state():
    """Test Process initialization and base state variables."""
    def dummy_func(proc):
        return "done"

    proc = CognitiveProcess(name="TestProc", target_func=dummy_func, priority=15)
    assert proc.id is not None
    assert proc.state == ProcessState.PENDING
    assert proc.priority == 15
    assert proc.execution_count == 0


def test_working_memory_isolation():
    """Test process-local working memory storage and isolation."""
    mem1 = WorkingMemory(process_id="p1")
    mem2 = WorkingMemory(process_id="p2")

    mem1.set("key", "val1")
    mem2.set("key", "val2")

    assert mem1.get("key") == "val1"
    assert mem2.get("key") == "val2"
    assert mem1.get_all() == {"key": "val1"}


def test_versioned_state_optimistic_concurrency():
    """Test VersionedState mutation with optimistic concurrency checks."""
    state = VersionedState(data="initial_state", version=1)

    # Valid mutation
    state.mutate("new_state", expected_version=1)
    assert state.data == "new_state"
    assert state.version == 2

    # Invalid mutation triggers ConcurrentUpdateError
    with pytest.raises(ConcurrentUpdateError):
        state.mutate("clashing_state", expected_version=1)


def test_resource_manifest_defaults_and_clamping():
    """Test Resource Manifest clamping process priority limits."""
    scheduler = Scheduler(event_logger=MagicMock())
    manifest = ResourceManifest(ceiling_priority=50)

    def dummy_func(proc):
        return "clamped"

    proc = CognitiveProcess(name="HighPriority", target_func=dummy_func, priority=90)
    scheduler.register_and_queue_process(proc, manifest=manifest)

    # Pop item from priority queue to verify actual priority used
    priority_val, _, _, queued_proc = scheduler._queue.get()
    # Inverted priority stored in python Queue
    assert priority_val == -50
    assert queued_proc.id == proc.id


def test_atomic_duration_enforcement():
    """Test YieldPoint enforces defined atomic limit thresholds."""
    yp = YieldPoint(atomic_limit_sec=0.01)
    yp.reset()

    # Initial check should pass immediately
    yp.check_and_enforce()

    # Sleep to breach limit
    time.sleep(0.015)
    with pytest.raises(AtomicDurationExceeded):
        yp.check_and_enforce()


def test_cooperative_yield_point_execution():
    """Test scheduler and process cooperative yield execution."""
    scheduler = Scheduler(event_logger=MagicMock())
    scheduler.atomic_limit_sec = 0.01  # Tight limit

    def long_running_cooperative_func(proc: CognitiveProcess):
        # First checkpoint passes
        proc.check_yield()
        time.sleep(0.015)
        # Second checkpoint should raise exception due to elapsed limit
        proc.check_yield()
        return "not_reached"

    proc = CognitiveProcess(name="LongCooperative", target_func=long_running_cooperative_func)
    scheduler.register_and_queue_process(proc)

    # Process next executes, gets yielded, and telemetry is updated accordingly
    scheduler.process_next()
    assert proc.state == ProcessState.YIELDED
    assert scheduler.telemetry.get_snapshot()["yields_triggered"] == 1


def test_anti_starvation_priority_bump():
    """Test that a process gets its priority bumped when it waits too long."""
    scheduler = Scheduler(event_logger=MagicMock())
    scheduler.starvation_threshold_sec = 0.005  # extremely low to easily trigger

    def dummy(proc):
        return "starving"

    proc = CognitiveProcess(name="StarvingProc", target_func=dummy, priority=10)
    scheduler.register_and_queue_process(proc)

    # Sleep so elapsed time is greater than starvation threshold
    time.sleep(0.01)

    # Run scheduler process_next to trigger anti-starvation pass
    # Since priority was 10 (inverted: -10), after bump it should be 30 (inverted: -30)
    scheduler._apply_anti_starvation()
    priority_val, _, _, popped_proc = scheduler._queue.get()
    assert priority_val == -30
    assert popped_proc.id == proc.id


def test_process_checkpointing_and_resume():
    """Test process milestone checkpoints and resume validation."""
    scheduler = Scheduler(event_logger=MagicMock())

    def dummy_func(proc):
        return "running"

    proc = CognitiveProcess(name="Stateful", target_func=dummy_func)
    scheduler.register_and_queue_process(proc)

    # Save state checkpoint
    scheduler.checkpoints.save_checkpoint(
        process_id=proc.id,
        checkpoint_id="milestone_1",
        version=5,
        memory_snapshot={"step": "A", "val": 10},
        milestone_name="StepACompleted",
    )

    # Failed resume with incorrect version
    assert not scheduler.resume_process_from_checkpoint(proc, "milestone_1", expected_version=4)

    # Successful resume with exact matching version validation
    assert scheduler.resume_process_from_checkpoint(proc, "milestone_1", expected_version=5)
    mem = scheduler.memories.get(proc.id)
    assert mem.get("step") == "A"
    assert mem.get("val") == 10


def test_commit_or_retry_semantics():
    """Test commit-or-retry state mutation outcomes and requeuing on conflict."""
    scheduler = Scheduler(event_logger=MagicMock())
    v_state = VersionedState(data="start", version=1)

    # Simulate success function
    def success_func(proc):
        return (v_state, "updated", 1)

    proc_success = CognitiveProcess(name="SuccessfulCommit", target_func=success_func)
    scheduler.register_and_queue_process(proc_success)
    scheduler.process_next()

    assert v_state.data == "updated"
    assert v_state.version == 2

    # Simulate conflict function (incorrect expected version triggers retry)
    def conflict_func(proc):
        return (v_state, "failed_mutate", 99)

    proc_conflict = CognitiveProcess(name="ConflictCommit", target_func=conflict_func)
    scheduler.register_and_queue_process(proc_conflict)
    scheduler.process_next()

    # Verify process has been requeued in scheduler queue for retrying
    assert scheduler.telemetry.get_snapshot()["retry_attempts"] == 1
    assert not scheduler._queue.empty()


def test_scheduler_degraded_mode():
    """Test scheduler skipping low-priority processes in degraded mode."""
    scheduler = Scheduler(event_logger=MagicMock())
    scheduler.enable_degraded_mode(True)

    def dummy(proc):
        return "run"

    low_proc = CognitiveProcess(name="Low", target_func=dummy, priority=20)
    high_proc = CognitiveProcess(name="High", target_func=dummy, priority=90)

    scheduler.register_and_queue_process(low_proc)
    scheduler.register_and_queue_process(high_proc)

    # Run scheduler - High priority should execute successfully, low priority blocked
    res_high = scheduler.process_next()
    res_low = scheduler.process_next()

    assert res_high == "run"
    assert res_low is None
    assert low_proc.state == ProcessState.BLOCKED


def test_local_real_time_interrupt_path():
    """Test pre-emptive interrupt execution path."""
    scheduler = Scheduler(event_logger=MagicMock())

    def dummy(proc):
        return "run"

    proc = CognitiveProcess(name="TargetProc", target_func=dummy, priority=10)
    scheduler.register_and_queue_process(proc)

    interrupt = LocalInterrupt(
        id="int_01",
        target_process_id=proc.id,
        severity=InterruptSeverity.CRITICAL,
        payload={"action": "re-evaluate"},
    )
    scheduler.trigger_local_interrupt(interrupt)

    # Execute scheduler loop
    scheduler.process_next()

    # Process table lookups and event queue should execute target immediately with high priority
    assert interrupt.handled
    assert scheduler.telemetry.get_snapshot()["interrupts_processed"] == 1


def test_telemetry_and_drift_detection():
    """Test Scheduler telemetry and manifest drift log tracking."""
    telemetry = TelemetryService()

    # Detect drift incident (allocated 1.0 CPU vs actual 2.0 CPU)
    has_drift = telemetry.detect_and_log_drift(
        process_id="p_01",
        allocated_cpu=1.0,
        actual_usage_cpu=2.0,
        threshold=0.5,
    )
    assert has_drift
    assert telemetry.metrics.drift_incidents == 1
    assert len(telemetry.get_drift_incidents()) == 1

    # Record guarantee violation
    telemetry.record_guarantee_violation("p_01", "deadline missed")
    assert telemetry.metrics.guarantee_violations == 1
