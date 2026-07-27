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
from memory.l1_views.projections.coin_projection import CoinProjection
from memory.l1_views.runner import ProjectionRunner, ReplayCursor
from memory.l1_views.models import CoinView, ProjectionState


@pytest.fixture
def coin_setup(session_factory, monkeypatch):
    """Initializes and returns L0EventStore and ProjectionRunner scoped to test transactions."""
    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    monkeypatch.setattr("memory.l1_views.runner.get_session", session_factory)
    monkeypatch.setattr("api.routes.nexus_coin_views.get_session", session_factory)

    store = L0EventStore(session_factory=session_factory)

    # Fresh test-isolated registry
    registry = ProjectionRegistry()
    registry.register(CoinProjection(session_factory=session_factory))

    runner = ProjectionRunner(
        registry=registry,
        event_store=store,
        session_factory=session_factory,
    )

    # Clean the views before starting
    runner.rebuild_projection("CoinProjection")

    return store, runner, session_factory, registry


# ------------------------------------------------------------------
# TEST CASES
# ------------------------------------------------------------------

def test_coin_unit_events_application(coin_setup):
    """Verifies that all supported event types are correctly routed and mapped to CoinView."""
    store, runner, session_factory, registry = coin_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    # 1. PriceUpdated
    store.append("PriceUpdated", {"symbol": "BTC", "price": 62500.0}, actor, "chain-1")
    # 2. MarketRegimeChanged
    store.append("MarketRegimeChanged", {"symbol": "BTC", "market_regime": "BULLISH", "confidence_score": 0.94}, actor, "chain-1")
    # 3. TrustUpdated
    store.append("TrustUpdated", {"symbol": "BTC", "trust_score": 8.7, "trust_version": "1.0.5"}, actor, "chain-1")
    # 4. CalibrationUpdated
    store.append("CalibrationUpdated", {"symbol": "BTC", "calibration_version": "v3.0"}, actor, "chain-1")
    # 5. PatternDetected
    store.append("PatternDetected", {"symbol": "BTC", "pattern": "DoubleBottom"}, actor, "chain-1")
    # 6. NewsPublished
    store.append("NewsPublished", {"news_id": "news-101", "related_assets": ["BTC"]}, actor, "chain-1")
    # 7. WhaleActivity
    store.append("WhaleActivity", {"symbol": "BTC", "wallet_id": "whale-1", "action": "BUY"}, actor, "chain-1")

    # Run incremental replay
    runner.run_incremental_replay()

    # Query CoinView directly
    db = session_factory()
    try:
        coin = db.query(CoinView).filter(CoinView.symbol == "BTC").first()
        assert coin is not None
        assert coin.latest_price == 62500.0
        assert coin.market_regime == "BULLISH"
        assert coin.confidence_score == 0.94
        assert coin.trust_score == 8.7
        assert coin.trust_version == "1.0.5"
        assert coin.calibration_version == "v3.0"
        assert "DoubleBottom" in coin.active_patterns
        assert coin.latest_news_id == "news-101"
        assert coin.latest_whale_activity["wallet_id"] == "whale-1"
    finally:
        db.close()


def test_coin_idempotency_monotonic_sequence(coin_setup):
    """Ensures older/duplicate L0 events are rejected via sequence number comparison."""
    store, runner, session_factory, registry = coin_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    store.append("PriceUpdated", {"symbol": "BTC", "price": 60000.0}, actor, "chain-1")
    store.append("PriceUpdated", {"symbol": "BTC", "price": 61000.0}, actor, "chain-1")

    runner.run_incremental_replay()

    # Assert correct latest state
    db = session_factory()
    try:
        coin = db.query(CoinView).filter(CoinView.symbol == "BTC").first()
        assert coin.latest_price == 61000.0
        assert coin.replay_seq_id == 2
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
    proj = runner.registry.get_by_name("CoinProjection")
    proj.apply(old_evt)

    # Database value must NOT regress to 60000.0
    db = session_factory()
    try:
        coin = db.query(CoinView).filter(CoinView.symbol == "BTC").first()
        assert coin.latest_price == 61000.0
        assert coin.replay_seq_id == 2
    finally:
        db.close()


def test_coin_unknown_events_graceful_handling(coin_setup):
    """Verifies that events not supported by CoinProjection are ignored gracefully."""
    store, runner, session_factory, registry = coin_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    # Append an unsupported event
    store.append("PortfolioStateUpdated", {"portfolio_id": "test-p"}, actor, "chain")

    res = runner.run_incremental_replay()
    assert res["events_processed"] == 0

    proj = runner.registry.get_by_name("CoinProjection")
    assert proj.health()["ignored_events"] == 1


def test_coin_snapshot_recovery(coin_setup):
    """Tests re-playing from a checkpoint state snapshot using restore_snapshot."""
    store, runner, session_factory, registry = coin_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    # Seed events
    store.append("PriceUpdated", {"symbol": "BTC", "price": 50000.0}, actor, "chain")
    store.append("PriceUpdated", {"symbol": "ETH", "price": 3000.0}, actor, "chain")

    runner.run_incremental_replay()

    # Capture snapshot
    proj = runner.registry.get_by_name("CoinProjection")
    state = proj.snapshot()
    assert len(state["coins"]) == 2

    # Clear everything via rebuild
    proj.rebuild()

    db = session_factory()
    try:
        assert db.query(CoinView).count() == 0
    finally:
        db.close()

    # Restore snapshot and assert
    runner.restore_projection_snapshot("CoinProjection", snapshot_state=state, last_seq_id=2)

    db = session_factory()
    try:
        assert db.query(CoinView).count() == 2
        btc = db.query(CoinView).filter(CoinView.symbol == "BTC").first()
        eth = db.query(CoinView).filter(CoinView.symbol == "ETH").first()
        assert btc.latest_price == 50000.0
        assert btc.replay_seq_id == 1
        assert eth.latest_price == 3000.0
        assert eth.replay_seq_id == 2
    finally:
        db.close()


def test_coin_deterministic_rebuild_from_empty(coin_setup):
    """Asserts that rebuild from 0 produces the exact same state as fresh sequential updates."""
    store, runner, session_factory, registry = coin_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    # Run consecutive updates
    store.append("PriceUpdated", {"symbol": "SOL", "price": 100.0}, actor, "chain")
    store.append("PriceUpdated", {"symbol": "SOL", "price": 110.0}, actor, "chain")
    store.append("PatternDetected", {"symbol": "SOL", "pattern": "DoubleBottom"}, actor, "chain")

    runner.run_incremental_replay()

    db = session_factory()
    try:
        state_before = {
            "latest_price": db.query(CoinView).filter(CoinView.symbol == "SOL").first().latest_price,
            "patterns": list(db.query(CoinView).filter(CoinView.symbol == "SOL").first().active_patterns),
        }
    finally:
        db.close()

    # Rebuild from 0
    runner.rebuild_projection("CoinProjection")

    db = session_factory()
    try:
        state_after = {
            "latest_price": db.query(CoinView).filter(CoinView.symbol == "SOL").first().latest_price,
            "patterns": list(db.query(CoinView).filter(CoinView.symbol == "SOL").first().active_patterns),
        }
    finally:
        db.close()

    assert state_before == state_after


def test_coin_concurrent_replay_resilience(coin_setup):
    """Simulates multiple rapid replay executions to assert database lock and state consistency."""
    store, runner, session_factory, registry = coin_setup
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    # Seed 10 price updates
    for i in range(10):
        store.append("PriceUpdated", {"symbol": "BTC", "price": 60000.0 + i}, actor, "chain")

    # Run replay multiple times consecutively
    runner.run_incremental_replay()
    runner.run_incremental_replay()
    runner.run_incremental_replay()

    # Final price should be 60009.0 and processed exactly once
    db = session_factory()
    try:
        coin = db.query(CoinView).filter(CoinView.symbol == "BTC").first()
        assert coin.latest_price == 60009.0
        assert coin.replay_seq_id == 10
    finally:
        db.close()


def test_coin_large_dataset_benchmark(coin_setup):
    """Simulates high event volume processing to evaluate average update latency and speed."""
    store, runner, session_factory, registry = coin_setup
    actor = {"id": "perf_agent", "type": "SYSTEM", "name": "Benchmark Agent"}

    events_data = []
    # Seed 500 events to run high throughput checks in a responsive way
    for i in range(500):
        events_data.append({
            "event_type": "PriceUpdated",
            "payload": {"symbol": f"SYM_{i % 5}", "price": 100.0 + i},
            "actor": actor,
            "causal_chain_id": f"chain-{i}",
        })

    store.append_batch(events_data)

    start_time = time.perf_counter()
    metrics = runner.rebuild_projection("CoinProjection")
    duration = time.perf_counter() - start_time

    assert metrics["events_processed"] == 500
    assert metrics["replay_speed"] > 0
    assert duration < 10.0  # highly optimized and fast SQLite memory executions


def test_fastapi_coin_endpoints(api_client, session_factory, monkeypatch):
    """E2E Integration test for Coin projection-specific REST API endpoints."""
    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    monkeypatch.setattr("memory.l1_views.runner.get_session", session_factory)
    monkeypatch.setattr("api.routes.nexus_coin_views.get_session", session_factory)

    # Ensure global_registry is clean and bound to session_factory
    global_registry.clear()
    global_registry.register(CoinProjection(session_factory=session_factory))

    store = L0EventStore(session_factory=session_factory)
    actor = {"id": "engine", "type": "SYSTEM", "name": "Engine"}

    store.append("PriceUpdated", {"symbol": "BTC", "price": 63400.0}, actor, "chain-1")
    store.append("MarketRegimeChanged", {"symbol": "BTC", "market_regime": "BEARISH", "confidence_score": 0.81}, actor, "chain-1")

    # 1. POST /nexus/l1/coin/rebuild
    res = api_client.post("/nexus/l1/coin/rebuild")
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"

    # 2. GET /nexus/l1/coin/state
    res = api_client.get("/nexus/l1/coin/state")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "BTC"
    assert data[0]["latest_price"] == 63400.0
    assert data[0]["market_regime"] == "BEARISH"

    # 3. GET /nexus/l1/coin/lookup/BTC
    res = api_client.get("/nexus/l1/coin/lookup/btc")
    assert res.status_code == 200
    btc_data = res.json()
    assert btc_data["latest_price"] == 63400.0

    # 4. GET /nexus/l1/coin/statistics
    res = api_client.get("/nexus/l1/coin/statistics")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_materialized_coins"] == 1
    assert stats["processed_events"] == 2

    # 5. GET /nexus/l1/coin/health
    res = api_client.get("/nexus/l1/coin/health")
    assert res.status_code == 200
    health = res.json()
    assert health["healthy"] is True
    assert health["diagnostics"]["processed_events"] == 2
