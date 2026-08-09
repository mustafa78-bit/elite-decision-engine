"""Unit tests for the Portfolio Engine.

Verifies all portfolio computations: equity, PnL, exposure, position
count, cash, win/loss tracking, equity curve, and drawdown.
"""

from datetime import UTC

import pytest

from database import (
    CANCEL,
    CLOSED,
    OPEN,
    SL_HIT,
    STOP_LOSS,
    TAKE_PROFIT,
    TP_HIT,
    PaperTrade,
    Trade,
)
from portfolio import PortfolioEngine, PortfolioSnapshot


def _make_trade(db_session, **overrides):
    signal_id = overrides.get("signal_id", 1)
    if signal_id is not None:
        from database import Signal
        existing_signal = db_session.query(Signal).filter(Signal.id == signal_id).first()
        if not existing_signal:
            sig = Signal(id=signal_id, symbol=overrides.get("symbol", "BTCUSDT"), side=overrides.get("side", "LONG"))
            db_session.add(sig)
            db_session.flush()
    kwargs = dict(
        signal_id=1,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49250.0,
        tp1=51000.0,
        status="OPEN",
        pnl=None,
    )
    kwargs.update(overrides)
    t = Trade(**kwargs)
    db_session.add(t)
    db_session.flush()
    return t


def _make_paper_trade(db_session, **overrides):
    kwargs = dict(
        position_id=1,
        order_id=1,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=1.0,
        pnl=0.0,
        status=OPEN,
    )
    kwargs.update(overrides)
    pt = PaperTrade(**kwargs)
    db_session.add(pt)
    db_session.flush()
    return pt


# ── Empty portfolio ────────────────────────────────────────────────────────


def test_empty_portfolio(session_factory):
    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()
    assert snap.total_equity == 10000.0
    assert snap.unrealized_pnl == 0.0
    assert snap.realized_pnl == 0.0
    assert snap.exposure == 0.0
    assert snap.long_exposure == 0.0
    assert snap.short_exposure == 0.0
    assert snap.position_count == 0
    assert snap.cash == 10000.0
    assert snap.total_trades == 0
    assert snap.win_rate == 0.0


# ── Single open LONG position ──────────────────────────────────────────────


def test_single_long_position(db_session, session_factory):
    trade = _make_trade(db_session, symbol="BTCUSDT", side="LONG")
    _make_paper_trade(
        db_session,
        position_id=trade.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=1.0,
        status=OPEN,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    assert snap.position_count == 1
    assert snap.exposure == 50000.0
    assert snap.long_exposure == 50000.0
    assert snap.short_exposure == 0.0
    assert snap.unrealized_pnl == 0.0  # no current_prices → uses entry
    assert snap.total_equity == 10000.0  # no PnL yet
    assert snap.cash == snap.total_equity - snap.exposure


# ── Single open LONG with custom price ─────────────────────────────────────


def test_long_unrealized_pnl(db_session, session_factory):
    trade = _make_trade(db_session, symbol="BTCUSDT", side="LONG")
    _make_paper_trade(
        db_session,
        position_id=trade.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=2.0,
        status=OPEN,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot(current_prices={"BTCUSDT": 52000.0})

    # (52000 - 50000) * 2.0 = 4000
    assert snap.unrealized_pnl == 4000.0
    assert snap.total_equity == 14000.0
    assert snap.exposure == 100000.0  # 50000 * 2.0


# ── Single open SHORT position ─────────────────────────────────────────────


def test_short_exposure_and_unrealized(db_session, session_factory):
    trade = _make_trade(db_session, symbol="ETHUSDT", side="SHORT")
    _make_paper_trade(
        db_session,
        position_id=trade.id,
        symbol="ETHUSDT",
        side="SHORT",
        entry=3000.0,
        quantity=5.0,
        status=OPEN,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot(current_prices={"ETHUSDT": 2800.0})

    assert snap.position_count == 1
    assert snap.exposure == 15000.0  # 3000 * 5
    assert snap.short_exposure == 15000.0
    assert snap.long_exposure == 0.0
    # SHORT: entry - current = 3000 - 2800 = 200 per unit × 5 = 1000
    assert snap.unrealized_pnl == 1000.0
    assert snap.total_equity == 11000.0


# ── Mixed long and short positions ─────────────────────────────────────────


def test_mixed_positions(db_session, session_factory):
    t1 = _make_trade(db_session, signal_id=1, symbol="BTCUSDT", side="LONG")
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=OPEN,
    )
    t2 = _make_trade(db_session, signal_id=2, symbol="ETHUSDT", side="SHORT")
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="ETHUSDT", side="SHORT",
        entry=3000.0, quantity=10.0, status=OPEN,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=20000.0,
    )
    snap = engine.snapshot(current_prices={"BTCUSDT": 51000.0, "ETHUSDT": 2900.0})

    assert snap.position_count == 2
    assert snap.long_exposure == 50000.0
    assert snap.short_exposure == 30000.0
    assert snap.exposure == 80000.0
    # LONG: (51000 - 50000) * 1 = 1000
    # SHORT: (3000 - 2900) * 10 = 1000
    assert snap.unrealized_pnl == 2000.0
    assert snap.total_equity == 22000.0


# ── Realized PnL from closed trades ───────────────────────────────────────


def test_realized_pnl(db_session, session_factory):
    # Trade.pnl is the field the real close path actually updates
    # (execution/paper_executor.py's _close_trade_record) -- PaperTrade.pnl
    # is never touched by it in production, so the fixture must set the real
    # per-unit value on the Trade for this to reflect reality.
    trade = _make_trade(db_session, status=TP_HIT, pnl=2000.0)
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=TAKE_PROFIT,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    assert snap.realized_pnl == 2000.0
    assert snap.total_equity == 12000.0
    assert snap.closed_trades == 1
    assert snap.winning_trades == 1


# ── Realized PnL with quantity multiplier ──────────────────────────────────


def test_realized_pnl_with_quantity(db_session, session_factory):
    trade = _make_trade(db_session, status=TP_HIT, pnl=1000.0)
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=2.0, status=TAKE_PROFIT,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    # 1000 per-unit * 2.0 quantity = 2000
    assert snap.realized_pnl == 2000.0
    assert snap.total_equity == 12000.0


# ── Win / loss tracking ────────────────────────────────────────────────────


def test_win_loss_tracking(db_session, session_factory):
    t1 = _make_trade(db_session, signal_id=1, status=TP_HIT, pnl=2000.0)
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=TAKE_PROFIT,
    )
    t2 = _make_trade(db_session, signal_id=2, status=SL_HIT, pnl=-1000.0)
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=STOP_LOSS,
    )
    t3 = _make_trade(db_session, signal_id=3, status=TP_HIT, pnl=500.0)
    _make_paper_trade(
        db_session, position_id=t3.id, symbol="ETHUSDT", side="SHORT",
        entry=3000.0, quantity=5.0, status=TAKE_PROFIT,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    assert snap.winning_trades == 2
    assert snap.losing_trades == 1
    assert snap.win_rate == 66.67
    assert snap.realized_pnl == (2000 + (-1000) + 2500)  # = 3500
    assert snap.total_equity == 13500.0
    assert snap.closed_trades == 3


# ── Cash calculation ────────────────────────────────────────────────────────


def test_cash_calculation(db_session, session_factory):
    trade = _make_trade(db_session, symbol="BTCUSDT", side="LONG")
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=OPEN,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot(current_prices={"BTCUSDT": 51000.0})

    # equity = 10000 + 1000 (unrealized) = 11000
    # exposure = 50000
    # cash = initial_capital + realized_pnl - exposure = 10000 + 0 - 50000 = -40000
    # (unrealized PnL is mark-to-market value tied up in the open position,
    # not spendable cash, so it must NOT be added to cash even though it's
    # part of total_equity)
    assert snap.total_equity == 11000.0
    assert snap.exposure == 50000.0
    assert snap.cash == -40000.0


# ── Profit factor ───────────────────────────────────────────────────────────


def test_profit_factor(db_session, session_factory):
    t1 = _make_trade(db_session, signal_id=1, status=TP_HIT, pnl=3000.0)
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=TAKE_PROFIT,
    )
    t2 = _make_trade(db_session, signal_id=2, status=SL_HIT, pnl=-1000.0)
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=STOP_LOSS,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    # gross_profit = 3000, gross_loss = 1000
    # profit_factor = 3000 / 1000 = 3.0
    assert snap.profit_factor == 3.0
    assert snap.realized_pnl == 2000.0


# ── Equity curve and drawdown ──────────────────────────────────────────────


def test_equity_curve_and_drawdown(db_session, session_factory):
    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )

    t1 = _make_trade(db_session, signal_id=1, status=TP_HIT, pnl=2000.0)
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=TAKE_PROFIT,
    )

    snap = engine.snapshot()
    assert len(snap.equity_curve) >= 2
    assert snap.equity_curve[0] == 10000.0
    assert snap.equity_curve[-1] == 12000.0
    assert snap.max_drawdown >= 0.0


# ── Mixed open and closed ──────────────────────────────────────────────────


def test_mixed_open_and_closed(db_session, session_factory):
    t1 = _make_trade(db_session, signal_id=1, symbol="BTCUSDT", side="LONG")
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=OPEN,
    )
    t2 = _make_trade(db_session, signal_id=2, status=TP_HIT, pnl=200.0)
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="ETHUSDT", side="LONG",
        entry=3000.0, quantity=10.0, status=TAKE_PROFIT,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=20000.0,
    )
    snap = engine.snapshot(current_prices={"BTCUSDT": 51000.0})

    assert snap.open_trades == 1
    assert snap.closed_trades == 1
    assert snap.total_trades == 2
    assert snap.unrealized_pnl == 1000.0  # (51000 - 50000) * 1
    assert snap.realized_pnl == 2000.0  # 200 * 10 = 2000
    assert snap.total_pnl == 3000.0
    assert snap.total_equity == 23000.0


# ── Default initial capital ────────────────────────────────────────────────


def test_default_initial_capital(session_factory):
    engine = PortfolioEngine(session_factory=session_factory)
    snap = engine.snapshot()
    assert snap.initial_capital == 10000.0
    assert snap.total_equity == 10000.0


# ── CANCEL status handled ──────────────────────────────────────────────────


def test_cancelled_trade_not_in_open(db_session, session_factory):
    trade = _make_trade(db_session, status=CANCEL)
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=0.0, status=CANCEL,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    assert snap.open_trades == 0
    assert snap.position_count == 0
    assert snap.exposure == 0.0


def test_equity_curve_ignores_trade_without_paper_trade(db_session, session_factory):
    # This test proves Bug 1 is fixed.
    # We construct a closed Trade that has a huge raw per-unit delta (pnl=500.0) but no matching PaperTrade.
    _make_trade(db_session, signal_id=1, status=TP_HIT, pnl=500.0)

    # We also construct a closed Trade with a matching PaperTrade that has a small real dollar PnL (pnl=10.0, qty=1.0)
    t_with_paper = _make_trade(db_session, signal_id=2, status=TP_HIT, pnl=10.0)
    _make_paper_trade(
        db_session,
        position_id=t_with_paper.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=1.0,
        pnl=10.0,
        status=TAKE_PROFIT,
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    # The equity curve should ONLY reflect the $10 real dollar PnL, not the $500 per-unit delta.
    # Initial: 10000.0, Trade 2: 10010.0. The trade without paper trade should be skipped entirely.
    assert len(snap.equity_curve) == 2
    assert snap.equity_curve[0] == 10000.0
    assert snap.equity_curve[1] == 10010.0
    assert snap.max_drawdown == 0.0


def test_metric_coverage_honesty(db_session, session_factory):
    # This test proves Bug 2 is fixed.
    # We create 3 closed Trade rows.
    # Only 1 of them has a matching PaperTrade with real PnL.
    # Trade.pnl (10.0, the real per-unit value the close path actually
    # writes) x PaperTrade.quantity (2.0) = 20.0 real dollar PnL.
    t1 = _make_trade(db_session, signal_id=1, status=TP_HIT, pnl=10.0)
    _make_paper_trade(
        db_session,
        position_id=t1.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=2.0,
        status=TAKE_PROFIT,
    )

    # Trades 2 and 3 do NOT have PaperTrade records.
    _make_trade(db_session, signal_id=2, status=SL_HIT, pnl=-5.0)
    _make_trade(db_session, signal_id=3, status=TP_HIT, pnl=15.0)

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    # We expect closed_trades to show 3.
    assert snap.closed_trades == 3
    # closed_trades_with_pnl should show 1.
    assert snap.closed_trades_with_pnl == 1
    # Realized PnL should reflect only the trade with the PaperTrade match ($20.0).
    assert snap.realized_pnl == 20.0
    # Winning and losing trades counts for metrics calculations should reflect only the PaperTrade subset.
    assert snap.winning_trades == 1
    assert snap.losing_trades == 0
    assert snap.win_rate == 100.0


def test_realized_pnl_counted_when_paper_trade_status_never_transitions(db_session, session_factory):
    # Matches real production exactly: execution/paper_executor.py's real
    # close path (_close_trade_record) only ever updates Trade.status/.pnl/
    # .closed_at -- the matching PaperTrade row's own .status is left at
    # whatever it was set to at open time (OPEN) forever, since nothing in
    # the real trading loop calls execution/paper.py's close_position(). A
    # position count / realized-PnL calculation keyed off PaperTrade.status
    # would treat this trade as permanently open and never count its profit.
    trade = _make_trade(db_session, status=TP_HIT, pnl=2000.0)
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, status=OPEN,  # never transitioned, as in real prod
    )

    engine = PortfolioEngine(
        session_factory=session_factory,
        initial_capital=10000.0,
    )
    snap = engine.snapshot()

    assert snap.open_trades == 0
    assert snap.closed_trades == 1
    assert snap.realized_pnl == 2000.0
    assert snap.winning_trades == 1


# ── Root PortfolioEngine (portfolio_engine.py) tests ────────────────────────


def test_root_portfolio_engine_unrealized_and_equity(db_session, session_factory):
    from database import Signal
    from portfolio_engine import PortfolioEngine as RootPortfolioEngine

    # Seed Signals to satisfy FK constraint on Trade.signal_id
    sig1 = Signal(id=101, symbol="BTCUSDT", side="LONG")
    sig2 = Signal(id=102, symbol="ETHUSDT", side="LONG")
    db_session.add(sig1)
    db_session.add(sig2)
    db_session.flush()

    # Open trade with positive unrealized pnl
    _make_trade(db_session, id=101, signal_id=101, symbol="BTCUSDT", status="OPEN", pnl=150.0)
    # Open trade with negative unrealized pnl
    _make_trade(db_session, id=102, signal_id=102, symbol="ETHUSDT", status="OPEN", pnl=-50.0)

    engine = RootPortfolioEngine(
        session_factory=session_factory,
        initial_equity=10000.0,
    )
    stats = engine.stats()

    # unrealized_pnl should be 150.0 + (-50.0) = 100.0
    assert stats.unrealized_pnl == 100.0
    # equity should be initial_equity + total_pnl + unrealized_pnl = 10000.0 + 0 + 100.0 = 10100.0
    assert stats.equity == 10100.0


def test_root_portfolio_engine_daily_pnl_timezone_aware(db_session, session_factory):
    from datetime import datetime, timezone

    from database import Signal
    from portfolio_engine import PortfolioEngine as RootPortfolioEngine

    # Seed Signal to satisfy FK constraint on Trade.signal_id
    sig1 = Signal(id=103, symbol="BTCUSDT", side="LONG")
    db_session.add(sig1)
    db_session.flush()

    # Closed trade with timezone-aware closed_at
    aware_now = datetime.now(UTC)
    _make_trade(
        db_session,
        id=103,
        signal_id=103,
        symbol="BTCUSDT",
        status="CLOSED",
        pnl=250.0,
        closed_at=aware_now,
    )

    engine = RootPortfolioEngine(
        session_factory=session_factory,
        initial_equity=10000.0,
    )

    # This should not raise "TypeError: can't compare offset-naive and offset-aware datetimes"
    stats = engine.stats()

    assert stats.daily_pnl == 250.0
    assert stats.total_pnl == 250.0
    assert stats.equity == 10250.0


def test_root_portfolio_engine_mixed_quantity_real_dollars(db_session, session_factory):
    from datetime import datetime, timedelta

    from portfolio_engine import PortfolioEngine as RootPortfolioEngine

    now = datetime.now(UTC)

    # BTC Trade (Win, closed)
    btc_trade = _make_trade(
        db_session,
        signal_id=10,
        symbol="BTCUSDT",
        side="LONG",
        entry=60000.0,
        pnl=500.0,
        status="CLOSED",
        created_at=now - timedelta(hours=4),
        closed_at=now - timedelta(hours=3),
    )
    _make_paper_trade(
        db_session,
        position_id=btc_trade.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=60000.0,
        exit_price=60500.0,
        quantity=0.01,
        pnl=500.0,
        status="CLOSED",
    )

    # ETH Trade (Loss, closed)
    eth_trade = _make_trade(
        db_session,
        signal_id=11,
        symbol="ETHUSDT",
        side="SHORT",
        entry=3000.0,
        pnl=-100.0,
        status="CLOSED",
        created_at=now - timedelta(hours=2),
        closed_at=now - timedelta(hours=1),
    )
    _make_paper_trade(
        db_session,
        position_id=eth_trade.id,
        symbol="ETHUSDT",
        side="SHORT",
        entry=3000.0,
        exit_price=3100.0,
        quantity=2.0,
        pnl=-100.0,
        status="CLOSED",
    )

    # SOL Trade (still OPEN, no matching PaperTrade -- exercises the qty=1.0 fallback)
    _make_trade(
        db_session,
        signal_id=12,
        symbol="SOLUSDT",
        side="LONG",
        entry=100.0,
        pnl=5.0,
        status="OPEN",
    )

    db_session.flush()

    engine = RootPortfolioEngine(
        session_factory=session_factory,
        initial_equity=10000.0,
    )
    stats = engine.stats()

    # Total Real PnL should be (500 * 0.01) + (-100 * 2.0) = 5.0 - 200.0 = -195.0
    assert stats.total_pnl == -195.0

    # Profit Factor should be gross_profit / gross_loss = 5.0 / 200.0 = 0.025 -> rounds to 0.03
    assert stats.profit_factor == 0.03

    # Equity Curve: [10000.0, 10005.0, 9805.0]
    assert stats.equity_curve == [10000.0, 10005.0, 9805.0]

    # Max Drawdown from peak (10005.0) to valley (9805.0)
    expected_dd = round(((10005.0 - 9805.0) / 10005.0) * 100, 2)
    assert stats.max_drawdown == expected_dd

    # Unrealized PnL: the OPEN SOL trade has no matching PaperTrade, so it
    # falls back to the raw per-unit value (quantity=1.0) -- 5.0.
    assert stats.unrealized_pnl == 5.0

    # equity = initial_equity + total_pnl + unrealized_pnl = 10000 - 195 + 5 = 9810
    assert stats.equity == 9810.0
