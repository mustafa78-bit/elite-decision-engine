"""Unit tests for the Portfolio Engine.

Verifies all portfolio computations: equity, PnL, exposure, position
count, cash, win/loss tracking, equity curve, and drawdown.
"""

import pytest

from portfolio import PortfolioEngine, PortfolioSnapshot
from database import (
    CLOSED,
    OPEN,
    STOP_LOSS,
    TAKE_PROFIT,
    TP_HIT,
    SL_HIT,
    CANCEL,
    PaperTrade,
    Trade,
)


def _make_trade(db_session, **overrides):
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
    trade = _make_trade(db_session, status=TP_HIT)
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=2000.0, status=TAKE_PROFIT,
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
    trade = _make_trade(db_session, status=TP_HIT)
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=2.0, pnl=1000.0, status=TAKE_PROFIT,
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
    t1 = _make_trade(db_session, signal_id=1, status=TP_HIT)
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=2000.0, status=TAKE_PROFIT,
    )
    t2 = _make_trade(db_session, signal_id=2, status=SL_HIT)
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=-1000.0, status=STOP_LOSS,
    )
    t3 = _make_trade(db_session, signal_id=3, status=TP_HIT)
    _make_paper_trade(
        db_session, position_id=t3.id, symbol="ETHUSDT", side="SHORT",
        entry=3000.0, quantity=5.0, pnl=500.0, status=TAKE_PROFIT,
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

    # equity = 10000 + 1000 = 11000
    # exposure = 50000
    # cash = 11000 - 50000 = -39000
    assert snap.total_equity == 11000.0
    assert snap.exposure == 50000.0
    assert snap.cash == snap.total_equity - snap.exposure


# ── Profit factor ───────────────────────────────────────────────────────────


def test_profit_factor(db_session, session_factory):
    t1 = _make_trade(db_session, signal_id=1, status=TP_HIT)
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=3000.0, status=TAKE_PROFIT,
    )
    t2 = _make_trade(db_session, signal_id=2, status=SL_HIT)
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=-1000.0, status=STOP_LOSS,
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

    t1 = _make_trade(db_session, signal_id=1, status=TP_HIT)
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=2000.0, status=TAKE_PROFIT,
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
    t2 = _make_trade(db_session, signal_id=2, status=TP_HIT)
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="ETHUSDT", side="LONG",
        entry=3000.0, quantity=10.0, pnl=200.0, status=TAKE_PROFIT,
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
