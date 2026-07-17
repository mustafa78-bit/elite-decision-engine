"""Unit tests for the RiskManager — every risk rule is tested in isolation."""

from datetime import datetime, timedelta, timezone

from database import Trade
from execution.pipeline import TradeCandidate
from risk_manager import RiskManager


class _MockSignal:
    def __init__(self, id=1):
        self.id = id


def _make_candidate(symbol="BTCUSDT", side="LONG", entry=50000.0, signal_id=1):
    return TradeCandidate(
        id=signal_id,
        symbol=symbol,
        side=side,
        timeframe="1h",
        entry=entry,
        scores={},
        confidence=0.9,
        decision="APPROVE",
        signal=_MockSignal(id=signal_id),
    )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _seed_trade(session, symbol="BTCUSDT", side="LONG", entry=50000.0, status="OPEN",
                pnl=0.0, closed_at=None, close_reason=None):
    trade = Trade(
        symbol=symbol,
        side=side,
        entry=entry,
        stop=entry * 0.98,
        tp1=entry * 1.02,
        rr=1.5,
        status=status,
        pnl=pnl,
        closed_at=closed_at,
        close_reason=close_reason,
    )
    session.add(trade)
    session.flush()
    return trade


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestRiskManager:

    def test_all_rules_pass(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is True
        assert reason == ""

    def test_reject_max_open_trades(self, db_session, session_factory):
        for _ in range(3):
            _seed_trade(db_session)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is False
        assert "Maximum open trades" in reason

    def test_invalid_symbol_rejection(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        candidate = _make_candidate(symbol=None)
        decision = mgr.evaluate_trade(candidate)
        assert decision.allowed is False
        assert decision.rejection_code == "INVALID_TRADE"
        assert "missing or invalid symbol" in decision.reason

        candidate = _make_candidate(symbol="   ")
        decision = mgr.evaluate_trade(candidate)
        assert decision.allowed is False
        assert decision.rejection_code == "INVALID_TRADE"

    def test_invalid_side_rejection(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        candidate = _make_candidate(side="UP")
        decision = mgr.evaluate_trade(candidate)
        assert decision.allowed is False
        assert decision.rejection_code == "INVALID_TRADE"
        assert "Side must be LONG or SHORT" in decision.reason

    def test_invalid_entry_rejection(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        candidate = _make_candidate(entry=0.0)
        decision = mgr.evaluate_trade(candidate)
        assert decision.allowed is True

        candidate = _make_candidate(entry=-100.0)
        decision = mgr.evaluate_trade(candidate)
        assert decision.allowed is False
        assert decision.rejection_code == "INVALID_TRADE"
        assert "Entry price cannot be negative" in decision.reason

    def test_evaluate_with_transactional_session(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        candidate = _make_candidate(entry=100.0)
        decision = mgr.evaluate_trade(candidate, session=db_session)
        assert decision.allowed is True
        assert decision.reason == ""

    def test_open_trade_limit_ignores_closed_trades(self, db_session, session_factory):
        _seed_trade(db_session, status="OPEN")
        _seed_trade(db_session, status="TP_HIT")
        _seed_trade(db_session, status="SL_HIT")
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is True

    def test_reject_symbol_exposure(self, db_session, session_factory):
        _seed_trade(db_session, symbol="BTCUSDT", entry=180000.0)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="BTCUSDT", entry=30000.0))
        assert allowed is False
        assert "Symbol exposure limit" in reason

    def test_allow_different_symbol(self, db_session, session_factory):
        _seed_trade(db_session, symbol="ETHUSDT", entry=180000.0)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="BTCUSDT", entry=50000.0))
        assert allowed is True

    def test_reject_portfolio_exposure(self, db_session, session_factory):
        _seed_trade(db_session, symbol="BTCUSDT", entry=300000.0)
        _seed_trade(db_session, symbol="ETHUSDT", entry=200000.0)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="SOLUSDT", entry=50000.0))
        assert allowed is False
        assert "Portfolio exposure limit" in reason

    def test_reject_daily_loss(self, db_session, session_factory):
        today = datetime.now(timezone.utc)
        _seed_trade(db_session, status="SL_HIT", pnl=-8000.0, closed_at=today, close_reason="SL_HIT")
        _seed_trade(db_session, status="SL_HIT", pnl=-3000.0, closed_at=today, close_reason="SL_HIT")
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is False
        assert "Daily loss limit" in reason

    def test_ignore_yesterdays_loss(self, db_session, session_factory):
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        _seed_trade(db_session, status="SL_HIT", pnl=-20000.0, closed_at=yesterday, close_reason="SL_HIT")
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is True

    def test_reject_position_size(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=150000.0))
        assert allowed is False
        assert "Position size limit" in reason


class TestRiskManagerEvaluateTrade:

    def test_returns_risk_decision(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        decision = mgr.evaluate_trade(_make_candidate(entry=50000.0))
        assert decision.allowed is True
        assert decision.reason == ""
        assert len(decision.checks) > 0

    def test_per_check_details_present(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        decision = mgr.evaluate_trade(_make_candidate(entry=50000.0))
        check_names = {c.name for c in decision.checks}
        assert "MAX_OPEN_TRADES" in check_names
        assert "SYMBOL_EXPOSURE" in check_names
        assert "PORTFOLIO_EXPOSURE" in check_names
        assert "DAILY_LOSS_LIMIT" in check_names
        assert "POSITION_SIZE_LIMIT" in check_names

    def test_check_values_populated(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        decision = mgr.evaluate_trade(_make_candidate(entry=50000.0))
        for c in decision.checks:
            assert c.passed is True
            assert c.detail == ""
            assert c.value is not None
            assert c.limit is not None

    def test_rejected_has_rejection_code(self, db_session, session_factory):
        for _ in range(3):
            _seed_trade(db_session)
        mgr = RiskManager(session_factory=session_factory)
        decision = mgr.evaluate_trade(_make_candidate(entry=50000.0))
        assert decision.allowed is False
        assert decision.rejection_code == "MAX_OPEN_TRADES"
        assert decision.reason != ""

    def test_all_checks_included_even_on_failure(self, db_session, session_factory):
        for _ in range(3):
            _seed_trade(db_session)
        mgr = RiskManager(session_factory=session_factory)
        decision = mgr.evaluate_trade(_make_candidate(entry=50000.0))
        assert len(decision.checks) == 1

    def test_backward_compat_can_open_trade_still_works(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is True
        assert reason == ""

    def test_backward_compat_rejected(self, db_session, session_factory):
        for _ in range(3):
            _seed_trade(db_session)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is False
        assert "Maximum open trades" in reason
