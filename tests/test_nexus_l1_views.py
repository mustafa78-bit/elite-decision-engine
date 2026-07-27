import time
import pytest
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi.testclient import TestClient
from api.main import app
from database import get_session
from memory.l0_event_log.service import L0EventStore
from memory.l0_event_log.models import NEXUSEvent
from memory.l1_views.base import BaseProjection
from memory.l1_views.registry import ProjectionRegistry, global_registry
from memory.l1_views.dispatcher import EventDispatcher
from memory.l1_views.runner import ProjectionRunner, ReplayCursor
from memory.l1_views.models import ProjectionState


# ------------------------------------------------------------------
# MOCK PROJECTIONS FOR INFRASTRUCTURE TESTING
# ------------------------------------------------------------------

class MockBaseProjection(BaseProjection):
    """A generic, fully-featured mock projection for testing framework infrastructure."""

    def __init__(self, name: str, event_types: List[str]) -> None:
        self._name = name
        self._event_types = event_types
        self.processed_ids: List[str] = []
        self.rebuild_called = False
        self.snapshot_data: Dict[str, Any] = {}
        self.is_healthy = True
        self.should_fail = False

    @property
    def projection_name(self) -> str:
        return self._name

    def supported_event_types(self) -> List[str]:
        return self._event_types

    def apply(self, event: NEXUSEvent) -> None:
        if self.should_fail:
            raise RuntimeError("Simulated projection application error")
        self.processed_ids.append(event.event_id)
        self.snapshot_data[event.event_id] = event.payload

    def rebuild(self) -> None:
        self.rebuild_called = True
        self.processed_ids.clear()
        self.snapshot_data.clear()

    def snapshot(self) -> Dict[str, Any]:
        return {"processed_ids": list(self.processed_ids), "data": dict(self.snapshot_data)}

    def restore_snapshot(self, state: Dict[str, Any]) -> None:
        self.processed_ids = list(state.get("processed_ids", []))
        self.snapshot_data = dict(state.get("data", {}))

    def validate(self) -> bool:
        return True

    def health(self) -> Dict[str, Any]:
        return {"status": "HEALTHY" if self.is_healthy else "DEGRADED", "custom_stat": 42}


# ------------------------------------------------------------------
# FIXTURE DEFINITIONS
# ------------------------------------------------------------------

@pytest.fixture
def framework_setup(session_factory, monkeypatch):
    """Sets up framework dependencies dynamically overriding database session bindings."""
    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    monkeypatch.setattr("memory.l1_views.runner.get_session", session_factory)
    monkeypatch.setattr("api.routes.nexus_l1_views.get_session", session_factory)

    store = L0EventStore(session_factory=session_factory)
    registry = ProjectionRegistry()
    dispatcher = EventDispatcher(registry=registry)
    runner = ProjectionRunner(
        registry=registry,
        dispatcher=dispatcher,
        event_store=store,
        session_factory=session_factory,
    )

    return store, registry, dispatcher, runner, session_factory


# ------------------------------------------------------------------
# TEST CASES
# ------------------------------------------------------------------

def test_registry_behavior_and_duplicate_prevention():
    """Verifies registry adds dynamically, resolves lookups, and blocks duplicates."""
    registry = ProjectionRegistry()

    p1 = MockBaseProjection(name="AuditProj", event_types=["EVENT_A"])
    p2 = MockBaseProjection(name="RiskProj", event_types=["EVENT_A", "EVENT_B"])

    registry.register(p1)
    registry.register(p2)

    # Resolve by name
    assert registry.get_by_name("AuditProj") is p1
    assert registry.get_by_name("RiskProj") is p2

    # Resolve by event type
    interested_in_a = registry.get_by_event_type("EVENT_A")
    assert p1 in interested_in_a
    assert p2 in interested_in_a

    interested_in_b = registry.get_by_event_type("EVENT_B")
    assert p1 not in interested_in_b
    assert p2 in interested_in_b

    # Duplicate registration prevention
    p_dup = MockBaseProjection(name="AuditProj", event_types=["EVENT_C"])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(p_dup)


def test_dispatcher_sequential_delivery_and_metrics(framework_setup):
    """Ensures EventDispatcher preserves event sequence and routes only to interested projections."""
    store, registry, dispatcher, runner, session_factory = framework_setup

    p_a = MockBaseProjection(name="ProjA", event_types=["EVENT_A"])
    p_b = MockBaseProjection(name="ProjB", event_types=["EVENT_B"])
    p_both = MockBaseProjection(name="ProjBoth", event_types=["EVENT_A", "EVENT_B"])

    registry.register(p_a)
    registry.register(p_b)
    registry.register(p_both)

    actor = {"id": "test", "type": "SYSTEM", "name": "Test"}
    evt1 = store.append("EVENT_A", {"index": 1}, actor, "chain-1")
    evt2 = store.append("EVENT_B", {"index": 2}, actor, "chain-1")

    # Dispatch event 1
    count1 = dispatcher.dispatch(evt1)
    assert count1 == 2  # ProjA, ProjBoth
    assert evt1.event_id in p_a.processed_ids
    assert evt1.event_id in p_both.processed_ids
    assert evt1.event_id not in p_b.processed_ids

    # Dispatch event 2
    count2 = dispatcher.dispatch(evt2)
    assert count2 == 2  # ProjB, ProjBoth
    assert evt2.event_id in p_b.processed_ids
    assert evt2.event_id in p_both.processed_ids
    assert evt2.event_id not in p_a.processed_ids

    # Metrics check
    metrics = dispatcher.get_metrics()
    assert metrics["processed_events"] == 2
    assert metrics["failed_events"] == 0


def test_idempotency_validation(framework_setup):
    """Asserts that older or duplicate events are ignored via sequence validation in ReplayCursor."""
    store, registry, dispatcher, runner, session_factory = framework_setup

    p = MockBaseProjection(name="TestProj", event_types=["EVENT_A"])
    registry.register(p)

    actor = {"id": "test", "type": "SYSTEM", "name": "Test"}
    evt1 = store.append("EVENT_A", {"index": 1}, actor, "chain-1")
    evt2 = store.append("EVENT_A", {"index": 2}, actor, "chain-1")

    cursor = ReplayCursor("TestProj", session_factory=session_factory)

    # First event is valid
    assert cursor.validate_sequence(evt1) is True
    # Simulate processing event 1
    cursor.update_checkpoint(seq_id=evt1.seq_id)

    # Second event is valid
    assert cursor.validate_sequence(evt2) is True
    # Simulate processing event 2
    cursor.update_checkpoint(seq_id=evt2.seq_id)

    # Re-evaluating event 1 should fail sequential validation (idempotent protection)
    assert cursor.validate_sequence(evt1) is False


def test_replay_cursor_database_checkpoints(framework_setup):
    """Ensures ReplayCursor persists checkpoints in database and does not rely on transient state."""
    store, registry, dispatcher, runner, session_factory = framework_setup

    cursor = ReplayCursor("StatefulProj", session_factory=session_factory)
    assert cursor.get_last_processed_seq_id() == 0

    cursor.update_checkpoint(seq_id=42, replay_cursor={"key": "val"})
    assert cursor.get_last_processed_seq_id() == 42

    # Query directly to ensure physical database persistence
    session = session_factory()
    try:
        record = session.query(ProjectionState).filter(ProjectionState.projection_name == "StatefulProj").first()
        assert record is not None
        assert record.last_processed_seq_id == 42
        assert record.replay_cursor == {"key": "val"}
    finally:
        session.close()


def test_projection_runner_replays(framework_setup):
    """Verifies full and incremental rebuild executions on a projection."""
    store, registry, dispatcher, runner, session_factory = framework_setup

    p = MockBaseProjection(name="ReplayProj", event_types=["EVENT_A", "EVENT_B"])
    registry.register(p)

    actor = {"id": "test", "type": "SYSTEM", "name": "Test"}
    store.append("EVENT_A", {"index": 1}, actor, "chain")
    store.append("EVENT_B", {"index": 2}, actor, "chain")
    store.append("EVENT_A", {"index": 3}, actor, "chain")

    # Run full rebuild
    res = runner.rebuild_projection("ReplayProj")
    assert res["events_processed"] == 3
    assert len(p.processed_ids) == 3

    # Append 2 more
    store.append("EVENT_B", {"index": 4}, actor, "chain")
    store.append("EVENT_A", {"index": 5}, actor, "chain")

    # Run incremental replay
    inc_res = runner.run_incremental_replay()
    assert inc_res["events_processed"] == 2
    assert len(p.processed_ids) == 5


def test_interruption_and_resume(framework_setup):
    """Simulates a failure during execution, ensuring the runner resumes from the exact checkpoint."""
    store, registry, dispatcher, runner, session_factory = framework_setup

    p = MockBaseProjection(name="ResilientProj", event_types=["EVENT_A"])
    registry.register(p)

    actor = {"id": "test", "type": "SYSTEM", "name": "Test"}
    store.append("EVENT_A", {"index": 1}, actor, "chain")
    store.append("EVENT_A", {"index": 2}, actor, "chain")
    store.append("EVENT_A", {"index": 3}, actor, "chain")

    # Process first event successfully
    runner.replay_projection(projection_name="ResilientProj", start_seq_id=1, end_seq_id=1)
    assert len(p.processed_ids) == 1

    # Simulate interruption/failure on event 2
    p.should_fail = True
    res = runner.replay_projection(projection_name="ResilientProj", start_seq_id=2, end_seq_id=3)
    assert res["events_processed"] == 0
    assert res["failed_events"] == 2
    assert len(p.processed_ids) == 1

    # Fix error and resume from checkpoint
    p.should_fail = False
    cursor = ReplayCursor("ResilientProj", session_factory=session_factory)
    checkpoint = cursor.get_last_processed_seq_id()
    assert checkpoint == 1

    # Replay resume picks up seq_id 2
    resume_res = runner.replay_projection(projection_name="ResilientProj", start_seq_id=checkpoint + 1)
    assert resume_res["events_processed"] == 2
    assert len(p.processed_ids) == 3


def test_snapshot_restoration(framework_setup):
    """Validates that Runner can restore snapshots and updates DB tracking to the snapshot sequence ID."""
    store, registry, dispatcher, runner, session_factory = framework_setup

    p = MockBaseProjection(name="SnapshotProj", event_types=["EVENT_A"])
    registry.register(p)

    snapshot_state = {
        "processed_ids": ["evt-101", "evt-102"],
        "data": {"evt-101": {"val": 10}, "evt-102": {"val": 20}},
    }

    runner.restore_projection_snapshot(
        projection_name="SnapshotProj",
        snapshot_state=snapshot_state,
        last_seq_id=150,
    )

    # In-memory restoration
    assert p.processed_ids == ["evt-101", "evt-102"]
    assert p.snapshot_data["evt-101"] == {"val": 10}

    # DB Checkpoint verification
    cursor = ReplayCursor("SnapshotProj", session_factory=session_factory)
    assert cursor.get_last_processed_seq_id() == 150


def test_fastapi_framework_routes(api_client, session_factory, monkeypatch):
    """E2E Integration test verifying all FastAPI framework endpoints using dynamic mock registrations."""
    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    monkeypatch.setattr("memory.l1_views.runner.get_session", session_factory)
    monkeypatch.setattr("api.routes.nexus_l1_views.get_session", session_factory)

    # Clear global registry for isolation
    global_registry.clear()

    # Dynamic registration check via API
    res = api_client.post("/nexus/l1/register-mock?name=WebAuditProj&event_types=SIGNAL_RECEIVED")
    assert res.status_code == 200
    assert res.json()["registered_name"] == "WebAuditProj"

    # List registered projections
    res = api_client.get("/nexus/l1/projections")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "WebAuditProj"

    # Fetch projection status
    res = api_client.get("/nexus/l1/status/WebAuditProj")
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["projection_name"] == "WebAuditProj"
    assert status_data["rebuild_status"] == "IDLE"

    # Replay action
    res = api_client.post("/nexus/l1/replay/WebAuditProj", json={"start_seq_id": 1})
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"

    # Rebuild action
    res = api_client.post("/nexus/l1/rebuild/WebAuditProj")
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"

    # Fetch metrics
    res = api_client.get("/nexus/l1/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["active_projection_count"] == 1

    # Fetch single health diagnostics
    res = api_client.get("/nexus/l1/health/WebAuditProj")
    assert res.status_code == 200
    health = res.json()
    assert health["healthy"] is True
    assert health["diagnostics"]["mock"] is True
