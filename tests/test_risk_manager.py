"""Unit tests for the RiskManager — every risk rule is tested in isolation."""

from datetime import UTC, datetime, timedelta, timezone

from database import PaperTrade, Trade
from execution.pipeline import TradeCandidate
from position_sizing import PositionSize
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
                pnl=0.0, closed_at=None, close_reason=None, quantity=None):
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

    if quantity is not None:
        paper_trade = PaperTrade(
            position_id=trade.id,
            symbol=symbol,
            side=side,
            entry=entry,
            quantity=quantity,
            status=status,
        )
        session.add(paper_trade)
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

    def test_open_trade_limit_ignores_closed_trades(self, db_session, session_factory):
        _seed_trade(db_session, status="OPEN")
        _seed_trade(db_session, status="TP_HIT")
        _seed_trade(db_session, status="SL_HIT")
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is True

    def test_reject_symbol_exposure(self, db_session, session_factory):
        _seed_trade(db_session, symbol="BTCUSDT", entry=180000.0, quantity=1.0)

        class MockSizer:
            def calculate(self, candidate):
                return PositionSize(quantity=1.0, notional_value=30000.0, risk_amount=0.0)

        mgr = RiskManager(session_factory=session_factory, position_sizer=MockSizer())
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="BTCUSDT", entry=30000.0))
        assert allowed is False
        assert "Symbol exposure limit" in reason

    def test_allow_different_symbol(self, db_session, session_factory):
        _seed_trade(db_session, symbol="ETHUSDT", entry=180000.0, quantity=1.0)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="BTCUSDT", entry=50000.0))
        assert allowed is True

    def test_reject_portfolio_exposure(self, db_session, session_factory):
        _seed_trade(db_session, symbol="BTCUSDT", entry=300000.0, quantity=1.0)
        _seed_trade(db_session, symbol="ETHUSDT", entry=200000.0, quantity=1.0)

        class MockSizer:
            def calculate(self, candidate):
                return PositionSize(quantity=1.0, notional_value=50000.0, risk_amount=0.0)

        mgr = RiskManager(session_factory=session_factory, position_sizer=MockSizer())
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="SOLUSDT", entry=50000.0))
        assert allowed is False
        assert "Portfolio exposure limit" in reason

    def test_btc_high_unit_price_small_real_position_passes_exposure(self, db_session, session_factory):
        # Existing open BTC trade: entry = 150,000.0, but quantity = 0.1 -> real notional = 15,000.0.
        # Well under MAX_EXPOSURE_PER_SYMBOL (200,000).
        _seed_trade(db_session, symbol="BTCUSDT", entry=150000.0, quantity=0.1)

        # Candidate BTC trade: entry = 150,000.0, but real position size notional = 15,000.0.
        class MockSizer:
            def calculate(self, candidate):
                return PositionSize(quantity=0.1, notional_value=15000.0, risk_amount=0.0)

        mgr = RiskManager(session_factory=session_factory, position_sizer=MockSizer())
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="BTCUSDT", entry=150000.0))

        # Under the old (raw-price) code: 150,000 + 150,000 = 300,000 > 200,000 -> false rejection.
        # Under the new (real-notional) code: 15,000 + 15,000 = 30,000 <= 200,000 -> correctly passes.
        assert allowed is True
        assert reason == ""

    def test_cheap_altcoin_large_real_position_trips_exposure(self, db_session, session_factory):
        # Existing open DOGE trade: entry = 0.1, but quantity = 2,500,000 -> real notional = 250,000.0,
        # already above MAX_EXPOSURE_PER_SYMBOL (200,000).
        _seed_trade(db_session, symbol="DOGEUSDT", entry=0.1, quantity=2500000.0)

        class MockSizer:
            def calculate(self, candidate):
                return PositionSize(quantity=100000.0, notional_value=10000.0, risk_amount=0.0)

        mgr = RiskManager(session_factory=session_factory, position_sizer=MockSizer())
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="DOGEUSDT", entry=0.1))

        # Under the old (raw-price) code: 0.1 + 0.1 = 0.2 <= 200,000 -> could never trip.
        # Under the new (real-notional) code: 250,000 + 10,000 = 260,000 > 200,000 -> correctly trips.
        assert allowed is False
        assert "Symbol exposure limit" in reason

    def test_reject_daily_loss(self, db_session, session_factory):
        today = datetime.now(UTC)
        # quantity=1.0 -> real dollar loss equals the raw pnl here; a
        # matching PaperTrade is required for these to count at all now that
        # orphaned (no-PaperTrade) trades are excluded rather than having
        # their raw per-unit pnl miscounted as dollar loss.
        _seed_trade(db_session, status="SL_HIT", pnl=-8000.0, closed_at=today, close_reason="SL_HIT", quantity=1.0)
        _seed_trade(db_session, status="SL_HIT", pnl=-3000.0, closed_at=today, close_reason="SL_HIT", quantity=1.0)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is False
        assert "Daily loss limit" in reason

    def test_ignore_yesterdays_loss(self, db_session, session_factory):
        yesterday = datetime.now(UTC) - timedelta(days=1)
        _seed_trade(db_session, status="SL_HIT", pnl=-20000.0, closed_at=yesterday, close_reason="SL_HIT")
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is True

    def test_no_rejection_for_high_unit_price(self, db_session, session_factory):
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=150000.0))
        assert allowed is True
        assert reason == ""

    def test_reject_daily_loss_uses_real_dollar_quantity(self, db_session, session_factory):
        today = datetime.now(UTC)
        # 3 closed trades today, each -2000 raw per-unit pnl, quantity=2 -> real dollar
        # loss = -2000 * 2 = -4000 each, -12000 total (> MAX_DAILY_LOSS of 10,000).
        # Raw per-unit sum alone would be -6000, under the 10,000 limit -> would have
        # wrongly passed under the old (unit-mismatched) code.
        for _ in range(3):
            _seed_trade(
                db_session, status="SL_HIT", pnl=-2000.0,
                closed_at=today, close_reason="SL_HIT", quantity=2.0,
            )
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is False
        assert "Daily loss limit" in reason

    def test_no_rejection_daily_loss_when_real_dollar_loss_is_small(self, db_session, session_factory):
        today = datetime.now(UTC)
        # A single closed trade with a large raw per-unit loss but a tiny real quantity:
        # raw pnl -9000, quantity=0.5 -> real dollar loss = -4500, under MAX_DAILY_LOSS.
        # Under the old (unit-mismatched) code, the raw -9000 alone would still pass
        # (under 10,000), but a second such trade would have wrongly tipped it over
        # 10,000 raw while still being well under 10,000 in real dollars -- prove the
        # real-dollar total (-9000) stays under the limit here.
        _seed_trade(
            db_session, status="SL_HIT", pnl=-9000.0,
            closed_at=today, close_reason="SL_HIT", quantity=0.5,
        )
        _seed_trade(
            db_session, status="SL_HIT", pnl=-9000.0,
            closed_at=today, close_reason="SL_HIT", quantity=0.5,
        )
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        # Real dollar loss: -9000*0.5 + -9000*0.5 = -9000, under 10,000 -> should pass.
        # Raw per-unit sum: -9000 + -9000 = -18000, would have wrongly rejected.
        assert allowed is True
        assert reason == ""

    def test_symbol_exposure_excludes_orphaned_trade_without_papertrade(self, db_session, session_factory):
        # Trade has no `quantity` column at all -- when the PaperTrade journal
        # write fails after the Trade commits (orphaning it), there is no real
        # way to know its real notional. A raw entry price of 250,000 alone
        # would, under the old code, get summed in as if it were already a
        # dollar notional -- permanently blocking any new BTCUSDT trade
        # regardless of real exposure. The fix excludes it instead of guessing.
        _seed_trade(db_session, symbol="BTCUSDT", entry=250000.0, quantity=None)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="BTCUSDT", entry=50000.0))
        assert allowed is True
        assert reason == ""

    def test_portfolio_exposure_excludes_orphaned_trade_without_papertrade(self, db_session, session_factory):
        _seed_trade(db_session, symbol="ETHUSDT", entry=600000.0, quantity=None)
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(symbol="BTCUSDT", entry=50000.0))
        assert allowed is True
        assert reason == ""

    def test_daily_loss_excludes_orphaned_trade_without_papertrade(self, db_session, session_factory):
        today = datetime.now(UTC)
        # Raw per-unit pnl of -50000 with no PaperTrade -- old code would sum
        # this directly as dollar loss and always reject; excluded instead.
        _seed_trade(
            db_session, status="SL_HIT", pnl=-50000.0,
            closed_at=today, close_reason="SL_HIT", quantity=None,
        )
        mgr = RiskManager(session_factory=session_factory)
        allowed, reason = mgr.can_open_trade(_make_candidate(entry=50000.0))
        assert allowed is True
        assert reason == ""


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
