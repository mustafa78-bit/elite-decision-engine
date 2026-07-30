from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.cognitive_scheduler import (
    CognitiveProcess,
    CognitiveScheduler,
    ResourceManifest,
    SharedVersionedQueue,
    ChannelScopedProcessTable,
    SchedulingGuaranteeViolation,
    VersionValidationError,
)


def test_process_memory_and_versions():
    """Test standard process memory updates, versioning, and optimistic concurrency."""
    proc = CognitiveProcess(
        process_id="proc_1",
        name="Trend Analysis",
        owner="OLLO",
        priority=3,
        manifest=ResourceManifest(max_duration_seconds=5.0)
    )
    assert proc.version == 1
    assert proc.state == "PENDING"

    # Valid optimistic concurrency update
    proc.update_memory({"trend": "BULLISH"}, expected_version=1)
    assert proc.version == 2
    assert proc.working_memory["trend"] == "BULLISH"

    # Invalid update (stale version)
    with pytest.raises(VersionValidationError):
        proc.update_memory({"trend": "BEARISH"}, expected_version=1)

    # Checkpoint and resume state
    proc.checkpoint({"step_idx": 42})
    assert proc.version == 3
    assert proc.checkpoint_data["step_idx"] == 42


def test_shared_versioned_queue():
    """Test thread-safe priority enqueuing, priority dequeuing, and version validation."""
    queue = SharedVersionedQueue()
    assert queue.version == 1

    proc_low = CognitiveProcess(process_id="low_prio", name="Low", owner="A", priority=10)
    proc_high = CognitiveProcess(process_id="high_prio", name="High", owner="B", priority=2)

    # Enqueue first
    expected_v = queue.version
    queue.enqueue(proc_low, expected_version=expected_v)
    assert queue.version == 2

    # Enqueue second with bad version
    with pytest.raises(VersionValidationError):
        queue.enqueue(proc_high, expected_version=1)

    # Valid enqueue
    queue.enqueue(proc_high, expected_version=queue.version)
    assert queue.version == 3

    # Dequeue retrieves high priority first
    dequeued = queue.dequeue(expected_version=queue.version)
    assert dequeued is not None
    assert dequeued.process_id == "high_prio"
    assert queue.version == 4

    # commit_or_retry transactional logic
    def test_tx(q_list):
        p = CognitiveProcess(process_id="tx_proc", name="Tx", owner="C", priority=5)
        q_list.append(p)
        return "added", q_list

    res = queue.commit_or_retry(test_tx)
    assert res == "added"
    assert queue.version == 5


def test_channel_scoped_process_table():
    """Test scoping processes across distinct channel keys."""
    table = ChannelScopedProcessTable()
    proc1 = CognitiveProcess(process_id="p1", name="A", owner="X")
    proc2 = CognitiveProcess(process_id="p2", name="B", owner="Y")

    table.register("scanners", proc1)
    table.register("trades", proc2)

    assert table.get_process("scanners", "p1") == proc1
    assert table.get_process("trades", "p2") == proc2
    assert table.get_process("scanners", "p2") is None

    assert len(table.get_active_processes("scanners")) == 1
    assert len(table.get_all_active_processes()) == 2


def test_cognitive_scheduler_violations_and_degraded_mode():
    """Test preemption, duration limits, drift detection, and degraded modes."""
    sched = CognitiveScheduler()
    proc = CognitiveProcess(
        process_id="p1",
        name="Long Task",
        owner="Tester",
        priority=8,
        manifest=ResourceManifest(max_duration_seconds=0.5, max_memory_mb=100.0)
    )

    sched.enqueue_process("default", proc)
    assert proc.state == "PENDING"

    # Test yield-point check when pending
    assert sched.yield_point(proc) is False

    # Execute step triggers memory drift detection (since memory consumption is simulated in step as +128.0MB, which exceeds 100MB limit)
    # And triggers Degraded Mode auto-activation
    assert sched.degraded_mode is False
    try:
        sched.execute_step("default")
    except SchedulingGuaranteeViolation:
        pass

    assert sched.degraded_mode is True
    assert len(sched.drift_alerts) == 1

    # In degraded mode, execute step raises SchedulingGuaranteeViolation and drops tasks with priority > 5
    proc_low = CognitiveProcess(process_id="low", name="Low", owner="Tester", priority=9)
    sched.enqueue_process("default", proc_low)
    with pytest.raises(SchedulingGuaranteeViolation, match="dropped"):
        sched.execute_step("default")

    assert proc_low.state == "FAILED"


def test_api_scheduler_observability_and_control(api_client):
    """Test FastAPI endpoint responses for SPRINT XII v2 scheduler features."""
    client = api_client

    # 1. Check status
    resp = client.get("/api/v1/scheduler/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    # 2. Enqueue process
    payload = {
        "process_id": "api_proc_1",
        "name": "API Test Task",
        "owner": "Jules",
        "priority": 4,
        "manifest": {
            "default_cpu_share": 0.5,
            "max_duration_seconds": 12.0,
            "max_memory_mb": 256.0
        },
        "channel_id": "scanners"
    }
    resp = client.post("/api/v1/scheduler/enqueue", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 3. Intercept & interrupt
    resp = client.post("/api/v1/scheduler/interrupt", json={"channel_id": "scanners", "process_id": "api_proc_1"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 4. Resume
    resp = client.post("/api/v1/scheduler/resume", json={"channel_id": "scanners", "process_id": "api_proc_1"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 5. Distributed synchronization sync
    sync_payload = {
        "node_id": "node_east_1",
        "processes": [
            {
                "process_id": "remote_proc_1",
                "name": "Remote Analysis",
                "owner": "OLLO Node",
                "priority": 3,
                "channel_id": "default"
            }
        ]
    }
    resp = client.post("/api/v1/scheduler/distributed/sync", json=sync_payload)
    assert resp.status_code == 200
    assert resp.json()["synced_count"] == 1
