"""Tests for SessionManager.save()/load() round-tripping full session state."""

from simulator.models import (
    SimulatedCandle,
    SimulatedDecision,
    SimulatedTrade,
    SimulatorConfig,
    SimulatorState,
    TimelineEvent,
)
from simulator.session_manager import SessionManager


def _build_populated_state() -> SimulatorState:
    state = SimulatorState(
        session_id="test-session-1",
        config=SimulatorConfig(symbol="BTC", timeframe="1h"),
        win_count=2,
        loss_count=1,
        total_pnl=123.45,
    )
    state.candles.append(
        SimulatedCandle(timestamp=1000, open=100.0, high=105.0, low=95.0, close=102.0, volume=10.0)
    )
    state.decisions.append(
        SimulatedDecision(
            id="dec-1",
            symbol="BTC",
            side="LONG",
            timestamp=1000,
            price=102.0,
            decision="APPROVE",
            confidence=0.9,
            evidence_strength=0.8,
            risk_score=0.2,
        )
    )
    state.trades.append(
        SimulatedTrade(
            id="trade-1",
            symbol="BTC",
            side="LONG",
            entry_price=102.0,
            entry_time=1000,
            quantity=1.0,
            leverage=1.0,
            stop_loss=95.0,
            take_profit=115.0,
        )
    )
    state.timeline.append(
        TimelineEvent(
            id="evt-1",
            timestamp=1000,
            event_type="TRADE_AI_OPEN",
            symbol="BTC",
            title="AI LONG BTC @ $102.0",
            description="opened",
        )
    )
    return state


def test_load_restores_all_collections_from_a_fresh_manager(tmp_path):
    saving_mgr = SessionManager(storage_dir=tmp_path)
    state = _build_populated_state()
    saving_mgr.save(state)

    # A brand-new SessionManager instance has an empty in-memory _sessions
    # cache, so this forces load() to actually read the saved JSON file
    # instead of short-circuiting on the cache hit at the top of load().
    loading_mgr = SessionManager(storage_dir=tmp_path)
    loaded = loading_mgr.load("test-session-1")

    assert loaded is not None
    assert loaded.win_count == 2
    assert loaded.loss_count == 1
    assert loaded.total_pnl == 123.45

    assert len(loaded.candles) == 1
    assert loaded.candles[0].close == 102.0

    assert len(loaded.decisions) == 1
    assert loaded.decisions[0].id == "dec-1"
    assert loaded.decisions[0].decision == "APPROVE"

    assert len(loaded.trades) == 1
    assert loaded.trades[0].id == "trade-1"
    assert loaded.trades[0].entry_price == 102.0

    assert len(loaded.timeline) == 1
    assert loaded.timeline[0].event_type == "TRADE_AI_OPEN"


def test_load_of_session_with_no_collections_returns_empty_lists(tmp_path):
    saving_mgr = SessionManager(storage_dir=tmp_path)
    state = SimulatorState(session_id="test-session-empty")
    saving_mgr.save(state)

    loading_mgr = SessionManager(storage_dir=tmp_path)
    loaded = loading_mgr.load("test-session-empty")

    assert loaded is not None
    assert loaded.candles == []
    assert loaded.decisions == []
    assert loaded.trades == []
    assert loaded.timeline == []
