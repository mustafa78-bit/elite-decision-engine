import time
import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi.testclient import TestClient
from api.main import app
from database import get_session
from memory.l0_event_log.service import L0EventStore
from memory.l0_event_log.models import NEXUSEvent
from memory.l1_views.registry import ProjectionRegistry, global_registry
from memory.l1_views.projections.whale_projection import WhaleProjection
from memory.l1_views.runner import ProjectionRunner, ReplayCursor
from memory.l1_views.models import WhaleView, ProjectionState


@pytest.fixture
def whale_setup(session_factory, monkeypatch):
    """Initializes and returns L0EventStore and ProjectionRunner scoped to test transactions."""
    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    monkeypatch.setattr("memory.l1_views.runner.get_session", session_factory)
    monkeypatch.setattr("api.routes.nexus_whale_views.get_session", session_factory)

    store = L0EventStore(session_factory=session_factory)

    # Fresh test-isolated registry
    registry = ProjectionRegistry()
    registry.register(WhaleProjection(session_factory=session_factory))

    runner = ProjectionRunner(
        registry=registry,
        event_store=store,
        session_factory=session_factory,
    )

    # Clean the views before starting
    runner.rebuild_projection("WhaleProjection")

    return store, runner, session_factory, registry


# ------------------------------------------------------------------
# TEST CASES
# ------------------------------------------------------------------

def test_whale_unit_events_application(whale_setup):
    """Verifies that WhaleActivity and WhaleTransaction events are correctly processed."""
    store, runner, session_factory, registry = whale_setup
    actor = {"id": "whale_radar", "type": "SYSTEM", "name": "Whale Radar"}

    # 1. WhaleActivity
    store.append(
        "WhaleActivity",
        {
            "wallet_id": "wallet-0x123",
            "accumulation_score": 90.0,
            "distribution_score": 10.0,
            "trust_score": 8.5,
            "exchange_distribution": {"Binance": 0.7},
        },
        actor,
        "chain-1",
    )

    # 2. WhaleTransaction (BUY SOL)
    store.append(
        "WhaleTransaction",
        {
            "wallet_id": "wallet-0x123",
            "realized_accuracy": 0.88,
            "asset": "SOL",
            "action": "BUY",
        },
        actor,
        "chain-1",
    )

    runner.run_incremental_replay()

    # Query WhaleView directly
    db = session_factory()
    try:
        w = db.query(WhaleView).filter(WhaleView.wallet_id == "wallet-0x123").first()
        assert w is not None
        assert w.total_events == 2
        assert w.accumulation_score == 90.0
        assert w.distribution_score == 10.0
        assert w.trust_score == 8.5
        assert w.exchange_distribution == {"Binance": 0.7}
        assert w.realized_accuracy == 0.88
        assert "SOL" in w.active_positions
    finally:
        db.close()

    # 3. WhaleTransaction (SELL SOL)
    store.append(
        "WhaleTransaction",
        {
            "wallet_id": "wallet-0x123",
            "asset": "SOL",
            "action": "SELL",
        },
        actor,
        "chain-1",
    )

    runner.run_incremental_replay()

    db = session_factory()
    try:
        w = db.query(WhaleView).filter(WhaleView.wallet_id == "wallet-0x123").first()
        assert "SOL" not in w.active_positions
        assert w.total_events == 3
    finally:
        db.close()


def test_whale_idempotency_monotonic_sequence(whale_setup):
    """Ensures older/duplicate L0 events are rejected via sequence number comparison."""
    store, runner, session_factory, registry = whale_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    store.append("WhaleActivity", {"wallet_id": "wallet-1", "accumulation_score": 50.0}, actor, "chain-1")
    store.append("WhaleActivity", {"wallet_id": "wallet-1", "accumulation_score": 60.0}, actor, "chain-1")

    runner.run_incremental_replay()

    # Assert correct latest state
    db = session_factory()
    try:
        w = db.query(WhaleView).filter(WhaleView.wallet_id == "wallet-1").first()
        assert w.accumulation_score == 60.0
        assert w.replay_seq_id == 2
        assert w.total_events == 2
    finally:
        db.close()

    # Manually fetch event 1 and try to apply it
    db = session_factory()
    try:
        old_evt = db.query(NEXUSEvent).filter(NEXUSEvent.seq_id == 1).first()
        db.expunge(old_evt)
    finally:
        db.close()

    # Re-apply old event
    proj = runner.registry.get_by_name("WhaleProjection")
    proj.apply(old_evt)

    # Database value must NOT regress
    db = session_factory()
    try:
        w = db.query(WhaleView).filter(WhaleView.wallet_id == "wallet-1").first()
        assert w.accumulation_score == 60.0
        assert w.replay_seq_id == 2
        # total_events should NOT have been incremented again
        assert w.total_events == 2
    finally:
        db.close()


def test_whale_unknown_events_graceful_handling(whale_setup):
    """Verifies that events not supported by WhaleProjection are ignored gracefully."""
    store, runner, session_factory, registry = whale_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    # Append an unsupported event
    store.append("PriceUpdated", {"symbol": "BTC", "price": 60000.0}, actor, "chain")

    res = runner.run_incremental_replay()
    assert res["events_processed"] == 0

    proj = runner.registry.get_by_name("WhaleProjection")
    assert proj.health()["ignored_events"] == 1


def test_whale_snapshot_recovery(whale_setup):
    """Tests re-playing from a checkpoint state snapshot using restore_snapshot."""
    store, runner, session_factory, registry = whale_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    store.append("WhaleActivity", {"wallet_id": "whale-a", "accumulation_score": 80.0}, actor, "chain")
    store.append("WhaleActivity", {"wallet_id": "whale-b", "accumulation_score": 90.0}, actor, "chain")

    runner.run_incremental_replay()

    # Capture snapshot
    proj = runner.registry.get_by_name("WhaleProjection")
    state = proj.snapshot()
    assert len(state["whales"]) == 2

    # Clear everything via rebuild
    proj.rebuild()

    db = session_factory()
    try:
        assert db.query(WhaleView).count() == 0
    finally:
        db.close()

    # Restore snapshot and assert
    runner.restore_projection_snapshot("WhaleProjection", snapshot_state=state, last_seq_id=2)

    db = session_factory()
    try:
        assert db.query(WhaleView).count() == 2
        w = db.query(WhaleView).filter(WhaleView.wallet_id == "whale-a").first()
        assert w.accumulation_score == 80.0
        assert w.replay_seq_id == 1
    finally:
        db.close()


def test_whale_large_dataset_benchmark(whale_setup):
    """Simulates high event volume processing to evaluate average update latency and speed."""
    store, runner, session_factory, registry = whale_setup
    actor = {"id": "perf_agent", "type": "SYSTEM", "name": "Benchmark Agent"}

    events_data = []
    # Seed 500 events
    for i in range(500):
        events_data.append({
            "event_type": "WhaleActivity",
            "payload": {"wallet_id": f"whale_wallet_{i % 5}", "accumulation_score": 10.0 + i},
            "actor": actor,
            "causal_chain_id": f"chain-{i}",
        })

    store.append_batch(events_data)

    start_time = time.perf_counter()
    metrics = runner.rebuild_projection("WhaleProjection")
    duration = time.perf_counter() - start_time

    assert metrics["events_processed"] == 500
    assert metrics["replay_speed"] > 0
    assert duration < 10.0


def test_fastapi_whale_endpoints(api_client, session_factory, monkeypatch):
    """E2E Integration test for Whale projection-specific REST API endpoints."""
    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    monkeypatch.setattr("memory.l1_views.runner.get_session", session_factory)
    monkeypatch.setattr("api.routes.nexus_whale_views.get_session", session_factory)

    # Ensure global_registry is clean and bound to session_factory
    global_registry.clear()
    global_registry.register(WhaleProjection(session_factory=session_factory))

    store = L0EventStore(session_factory=session_factory)
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    store.append("WhaleActivity", {"wallet_id": "whale-vip", "accumulation_score": 95.5}, actor, "chain-1")

    # 1. POST /nexus/l1/whale/rebuild
    res = api_client.post("/nexus/l1/whale/rebuild")
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"

    # 2. GET /nexus/l1/whale/state
    res = api_client.get("/nexus/l1/whale/state")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["wallet_id"] == "whale-vip"
    assert data[0]["accumulation_score"] == 95.5

    # 3. GET /nexus/l1/whale/lookup/whale-vip
    res = api_client.get("/nexus/l1/whale/lookup/whale-vip")
    assert res.status_code == 200
    w_data = res.json()
    assert w_data["accumulation_score"] == 95.5

    # 4. GET /nexus/l1/whale/statistics
    res = api_client.get("/nexus/l1/whale/statistics")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_materialized_whales"] == 1
    assert stats["processed_events"] == 1

    # 5. GET /nexus/l1/whale/health
    res = api_client.get("/nexus/l1/whale/health")
    assert res.status_code == 200
    health = res.json()
    assert health["healthy"] is True
    assert health["diagnostics"]["processed_events"] == 1
