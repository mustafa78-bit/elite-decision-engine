import time
import pytest
from datetime import datetime, timezone
from memory.l0_event_log.service import L0EventStore
from memory.l0_event_log.models import NEXUSEvent, NEXUSSnapshot


@pytest.fixture
def store(db_session, monkeypatch):
    """Fixture that initializes the L0EventStore with a test database session."""
    # Monkeypatch the get_session inside L0EventStore to use our test session
    def session_factory():
        return db_session

    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    return L0EventStore(session_factory=session_factory)


def test_append_single_event_and_provenance(store, db_session):
    """Test appending a single event with valid actor, payload, and provenance link."""
    actor = {"id": "agent_test", "type": "AGENT", "name": "Agent Test"}
    payload = {"symbol": "BTC", "price": 65000.0, "reason": "EMA cross"}
    chain_id = "chain-uuid-1"

    # Append first event
    evt1 = store.append(
        event_type="SIGNAL_RECEIVED",
        payload=payload,
        actor=actor,
        causal_chain_id=chain_id,
    )

    assert evt1.event_id is not None
    assert evt1.seq_id == 1
    assert evt1.event_type == "SIGNAL_RECEIVED"
    assert evt1.payload == payload
    assert evt1.causal_chain_id == chain_id
    assert evt1.parent_event_id is None
    assert evt1.checksum is not None

    # Append second event linked to the first
    evt2 = store.append(
        event_type="DECISION_EXPLANATION_GENERATED",
        payload={"decision": "BUY", "confidence": 0.85},
        actor=actor,
        causal_chain_id=chain_id,
        parent_event_id=evt1.event_id,
    )

    assert evt2.seq_id == 2
    assert evt2.parent_event_id == evt1.event_id


def test_append_batch(store):
    """Test appending multiple events in a single transaction."""
    actor = {"id": "batch_runner", "type": "SYSTEM", "name": "Batch System"}
    chain_id = "chain-uuid-batch"

    events_data = [
        {
            "event_type": "SIGNAL_RECEIVED",
            "payload": {"price": 100},
            "actor": actor,
            "causal_chain_id": chain_id,
        },
        {
            "event_type": "RISK_CHECKED",
            "payload": {"allowed": True},
            "actor": actor,
            "causal_chain_id": chain_id,
        },
    ]

    persisted = store.append_batch(events_data)
    assert len(persisted) == 2
    assert persisted[0].seq_id == 1
    assert persisted[1].seq_id == 2
    assert persisted[0].checksum != persisted[1].checksum


def test_event_replay_and_state_reconstruction(store):
    """Test replaying chronological events to reconstruct current state."""
    actor = {"id": "portfolio_tracker", "type": "SYSTEM", "name": "Tracker"}
    chain_id = "portfolio-chain"

    # Append events representing sequential ledger changes
    store.append("DEPOSIT", {"balance": 1000}, actor, chain_id)
    store.append("TRADE_BUY", {"balance": 800, "positions": ["BTC"]}, actor, chain_id)
    store.append("TRADE_SELL", {"balance": 1100, "positions": []}, actor, chain_id)

    # Reconstruct state using default reducer (merges payloads)
    final_state = store.replay_events(causal_chain_id=chain_id)
    assert final_state["balance"] == 1100
    assert final_state["positions"] == []


def test_state_snapshot(store):
    """Test saving and retrieving state snapshots to bypass replay from scratch."""
    chain_id = "snapshot-chain"
    state = {"balance": 5000, "assets": ["BTC", "ETH"]}

    # Create snapshot up to seq_id 15
    snap = store.create_snapshot(causal_chain_id=chain_id, last_seq_id=15, state=state)

    assert snap.snapshot_id is not None
    assert snap.causal_chain_id == chain_id
    assert snap.last_seq_id == 15
    assert snap.state == state
    assert snap.checksum is not None

    # Retrieve latest snapshot
    retrieved = store.get_latest_snapshot(chain_id)
    assert retrieved is not None
    assert retrieved.snapshot_id == snap.snapshot_id
    assert retrieved.state == state


def test_streaming_and_paginated_reads(store):
    """Test pagination filters and streaming generator chunks."""
    actor = {"id": "streamer", "type": "SYSTEM", "name": "Streamer"}
    chain_id = "stream-chain"

    # Generate 15 dummy events
    for i in range(15):
        store.append("TICK", {"index": i}, actor, chain_id)

    # Read events with limits
    batch1 = store.read_events(start_seq_id=1, limit=10)
    assert len(batch1) == 10
    assert batch1[0].seq_id == 1
    assert batch1[-1].seq_id == 10

    # Stream generator
    stream_generator = store.stream_events(start_seq_id=1, chunk_size=4)
    streamed_events = list(stream_generator)
    assert len(streamed_events) == 15
    assert streamed_events[0].seq_id == 1
    assert streamed_events[-1].seq_id == 15


def test_integrity_verification_and_corruption_quarantine(store, db_session):
    """Test cryptographic SHA-256 detection and quarantining of tampered logs."""
    actor = {"id": "audit_actor", "type": "SYSTEM", "name": "Audit"}
    chain_id = "audit-chain"

    evt1 = store.append("EVENT_A", {"secret_val": 42}, actor, chain_id)
    evt2 = store.append("EVENT_B", {"secret_val": 84}, actor, chain_id)

    # Verify initially healthy
    corrupted_before, quarantined_before = store.verify_integrity()
    assert len(corrupted_before) == 0

    # Manually tamper with the database record to simulate a security breach/corruption
    db_session.query(NEXUSEvent).filter(NEXUSEvent.event_id == evt2.event_id).update(
        {"payload": {"secret_val": 99999}}
    )
    db_session.commit()

    # Re-verify and assert corruption detection
    corrupted_after, quarantined_after = store.verify_integrity()
    assert evt2.event_id in corrupted_after
    assert evt2.event_id in quarantined_after

    # Verify that the corrupted event has been quarantined
    evt2_reloaded = store.get_event(evt2.event_id)
    assert evt2_reloaded.is_quarantined is True
    assert "Checksum mismatch" in evt2_reloaded.quarantine_reason

    # Query normal reads and assert quarantined event is safely omitted
    healthy_reads = store.read_events(include_quarantined=False)
    assert len(healthy_reads) == 1
    assert healthy_reads[0].event_id == evt1.event_id


def test_performance_benchmarks(store):
    """Benchmark performance for write and replay operations."""
    actor = {"id": "benchmark_actor", "type": "SYSTEM", "name": "Benchmark"}
    chain_id = "bench-chain"

    # Write Benchmark
    start_write = time.perf_counter()
    for i in range(100):
        store.append("PERF_TICK", {"index": i}, actor, chain_id)
    write_duration = time.perf_counter() - start_write

    # Replay Benchmark
    start_replay = time.perf_counter()
    reconstructed_state = store.replay_events(chain_id)
    replay_duration = time.perf_counter() - start_replay

    print(f"L0 Performance Benchmarks: Writes={write_duration:.4f}s, Replay={replay_duration:.4f}s")
    assert write_duration < 10.0  # Must be fast
    assert replay_duration < 2.0
    assert reconstructed_state["index"] == 99
