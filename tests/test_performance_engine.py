"""Unit tests for the Performance Engine.

Verifies: Sharpe, Sortino, Calmar, Average Win/Loss, Expectancy,
Payoff Ratio, Recovery Factor, Largest Win/Loss, Consecutive
Wins/Losses, Average Holding Time, Trade Frequency.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from database import (
    CLOSED,
    STOP_LOSS,
    TAKE_PROFIT,
    CANCEL,
    PaperTrade,
    Trade,
)
from performance import PerformanceEngine, PerformanceReport
from portfolio.core import PortfolioSnapshot

_INFINITE = 999.99


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
        status="OPEN",
    )
    kwargs.update(overrides)
    pt = PaperTrade(**kwargs)
    db_session.add(pt)
    db_session.flush()
    return pt


# ── Empty portfolio ────────────────────────────────────────────────────────


def test_empty(session_factory):
    engine = PerformanceEngine(session_factory=session_factory)
    snap = PortfolioSnapshot()
    report = engine.report(snap)
    assert report.sharpe_ratio == 0.0
    assert report.sortino_ratio == 0.0
    assert report.calmar_ratio == 0.0
    assert report.average_win == 0.0
    assert report.average_loss == 0.0
    assert report.expectancy == 0.0
    assert report.payoff_ratio == 0.0
    assert report.recovery_factor == 0.0
    assert report.largest_win == 0.0
    assert report.largest_loss == 0.0
    assert report.consecutive_wins == 0
    assert report.consecutive_losses == 0
    assert report.average_holding_time_hours == 0.0
    assert report.trade_frequency_per_day == 0.0


# ── Single winning trade ────────────────────────────────────────────────────


def test_single_win(db_session, session_factory):
    now = datetime.now(timezone.utc)
    trade = _make_trade(
        db_session, status="TP_HIT", pnl=2000.0,
        created_at=now - timedelta(hours=24),
        closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=2000.0, status=TAKE_PROFIT,
    )

    snap = PortfolioSnapshot(
        total_equity=12000.0,
        initial_capital=10000.0,
        total_pnl=2000.0,
        realized_pnl=2000.0,
        equity_curve=[10000.0, 12000.0],
        max_drawdown=0.0,
        closed_trades=1,
        winning_trades=1,
        losing_trades=0,
        win_rate=100.0,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    assert report.average_win == 2000.0
    assert report.largest_win == 2000.0
    assert report.average_loss == 0.0
    assert report.largest_loss == 0.0
    assert report.consecutive_wins == 1
    assert report.consecutive_losses == 0
    assert report.average_holding_time_hours == 24.0
    assert report.trade_frequency_per_day > 0
    # Zero drawdown + positive return → infinite ratios
    assert report.calmar_ratio == _INFINITE
    assert report.recovery_factor == _INFINITE


# ── Single loss ──────────────────────────────────────────────────────────────


def test_single_loss(db_session, session_factory):
    now = datetime.now(timezone.utc)
    trade = _make_trade(
        db_session, status="SL_HIT", pnl=-1000.0,
        created_at=now - timedelta(hours=12),
        closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=trade.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=-1000.0, status=STOP_LOSS,
    )

    snap = PortfolioSnapshot(
        total_equity=9000.0,
        initial_capital=10000.0,
        total_pnl=-1000.0,
        realized_pnl=-1000.0,
        equity_curve=[10000.0, 9000.0],
        max_drawdown=10.0,
        closed_trades=1,
        winning_trades=0,
        losing_trades=1,
        win_rate=0.0,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    assert report.average_loss == -1000.0
    assert report.largest_loss == -1000.0
    assert report.average_win == 0.0
    assert report.consecutive_losses == 1
    assert report.average_holding_time_hours == 12.0
    # Negative return + positive drawdown = negative calmar
    assert report.calmar_ratio < 0
    assert report.recovery_factor < 0


# ── Mixed wins and losses ────────────────────────────────────────────────────


def test_mixed_trades(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="TP_HIT", pnl=3000.0,
        created_at=now - timedelta(hours=48), closed_at=now - timedelta(hours=24),
    )
    _make_paper_trade(
        db_session, position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=3000.0, status=TAKE_PROFIT,
    )
    t2 = _make_trade(
        db_session, signal_id=2, status="SL_HIT", pnl=-1000.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t2.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=1.0, pnl=-1000.0, status=STOP_LOSS,
    )

    snap = PortfolioSnapshot(
        total_equity=12000.0,
        initial_capital=10000.0,
        total_pnl=2000.0,
        realized_pnl=2000.0,
        equity_curve=[10000.0, 13000.0, 12000.0],
        max_drawdown=7.69,
        closed_trades=2,
        winning_trades=1,
        losing_trades=1,
        win_rate=50.0,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    assert report.average_win == 3000.0
    assert report.average_loss == -1000.0
    assert report.expectancy == 1000.0  # 0.5*3000 - 0.5*1000 = 1000
    assert report.payoff_ratio == 3.0  # 3000 / 1000
    assert report.largest_win == 3000.0
    assert report.largest_loss == -1000.0
    assert report.consecutive_wins == 1
    assert report.consecutive_losses == 1
    assert report.sharpe_ratio != 0.0
    assert report.sortino_ratio != 0.0
    assert report.calmar_ratio != 0.0


# ── Consecutive streaks ──────────────────────────────────────────────────────


def test_consecutive_streaks(db_session, session_factory):
    now = datetime.now(timezone.utc)
    results = [2000.0, 1500.0, 1000.0, -500.0, -300.0, 2500.0, -800.0]
    trades = []
    for i, pnl in enumerate(results):
        t = _make_trade(
            db_session, signal_id=i + 1, status="TP_HIT" if pnl > 0 else "SL_HIT",
            pnl=pnl,
            created_at=now - timedelta(hours=len(results) - i),
            closed_at=now - timedelta(hours=len(results) - 1 - i),
        )
        trades.append(t)
        _make_paper_trade(
            db_session, position_id=t.id, symbol="BTCUSDT", side="LONG",
            entry=50000.0, quantity=1.0, pnl=pnl,
            status=TAKE_PROFIT if pnl > 0 else STOP_LOSS,
        )

    # Build equity curve
    eq = [10000.0]
    for p in results:
        eq.append(eq[-1] + p)

    snap = PortfolioSnapshot(
        total_equity=eq[-1],
        initial_capital=10000.0,
        total_pnl=sum(results),
        realized_pnl=sum(results),
        equity_curve=eq,
        max_drawdown=5.0,
        closed_trades=len(results),
        winning_trades=4,
        losing_trades=3,
        win_rate=57.14,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    # Streaks: wins=3 (+2000,+1500,+1000), losses=2 (-500,-300), win=1 (+2500), loss=1 (-800)
    assert report.consecutive_wins == 3
    assert report.consecutive_losses == 2


# ── Holding time and frequency ──────────────────────────────────────────────


def test_holding_time_and_frequency(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="TP_HIT", pnl=1000.0,
        created_at=now - timedelta(hours=48), closed_at=now - timedelta(hours=24),
    )
    _make_paper_trade(
        db_session, position_id=t1.id, quantity=1.0, pnl=1000.0, status=TAKE_PROFIT,
    )
    t2 = _make_trade(
        db_session, signal_id=2, status="TP_HIT", pnl=500.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t2.id, quantity=1.0, pnl=500.0, status=TAKE_PROFIT,
    )

    snap = PortfolioSnapshot(
        total_equity=11500.0,
        initial_capital=10000.0,
        total_pnl=1500.0,
        realized_pnl=1500.0,
        equity_curve=[10000.0, 11000.0, 11500.0],
        max_drawdown=0.0,
        closed_trades=2,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    # t1: 24h, t2: 24h → avg = 24h
    assert report.average_holding_time_hours == 24.0
    # span = 48h = 2 days, 2 trades → 1 per day
    assert report.trade_frequency_per_day == 1.0


# ── Payoff ratio edge cases ─────────────────────────────────────────────────


def test_payoff_ratio_all_wins(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="TP_HIT", pnl=500.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t1.id, quantity=1.0, pnl=500.0, status=TAKE_PROFIT,
    )

    snap = PortfolioSnapshot(
        total_equity=10500.0,
        initial_capital=10000.0,
        total_pnl=500.0,
        realized_pnl=500.0,
        equity_curve=[10000.0, 10500.0],
        max_drawdown=0.0,
        closed_trades=1,
        winning_trades=1,
        losing_trades=0,
        win_rate=100.0,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    assert report.average_loss == 0.0
    # avg_win=500, avg_loss=0 → infinite payoff ratio
    assert report.payoff_ratio == _INFINITE


# ── Expectancy edge cases ──────────────────────────────────────────────────


def test_expectancy_all_losses(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="SL_HIT", pnl=-500.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t1.id, quantity=1.0, pnl=-500.0, status=STOP_LOSS,
    )

    snap = PortfolioSnapshot(
        total_equity=9500.0,
        initial_capital=10000.0,
        total_pnl=-500.0,
        realized_pnl=-500.0,
        equity_curve=[10000.0, 9500.0],
        max_drawdown=5.0,
        closed_trades=1,
        winning_trades=0,
        losing_trades=1,
        win_rate=0.0,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    assert report.average_win == 0.0
    assert report.average_loss == -500.0
    assert report.expectancy == -500.0  # 0 - 1.0*500 = -500
    assert report.largest_win == 0.0
    assert report.largest_loss == -500.0


# ── Sharpe / Sortino with flat equity curve ─────────────────────────────────


def test_sharpe_sortino_flat(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="TP_HIT", pnl=0.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t1.id, quantity=1.0, pnl=0.0, status=TAKE_PROFIT,
    )

    snap = PortfolioSnapshot(
        total_equity=10000.0,
        initial_capital=10000.0,
        total_pnl=0.0,
        realized_pnl=0.0,
        equity_curve=[10000.0, 10000.0],
        max_drawdown=0.0,
        closed_trades=1,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    assert report.sharpe_ratio == 0.0
    assert report.sortino_ratio == 0.0
    assert report.calmar_ratio == 0.0


# ── Recovery factor with drawdown ────────────────────────────────────────────


def test_recovery_factor(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="SL_HIT", pnl=-2000.0,
        created_at=now - timedelta(hours=48), closed_at=now - timedelta(hours=24),
    )
    _make_paper_trade(
        db_session, position_id=t1.id, quantity=1.0, pnl=-2000.0, status=STOP_LOSS,
    )
    t2 = _make_trade(
        db_session, signal_id=2, status="TP_HIT", pnl=3000.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t2.id, quantity=1.0, pnl=3000.0, status=TAKE_PROFIT,
    )

    # peak = 10000, drop to 8000 (20% dd), recover to 11000
    snap = PortfolioSnapshot(
        total_equity=11000.0,
        initial_capital=10000.0,
        total_pnl=1000.0,
        realized_pnl=1000.0,
        equity_curve=[10000.0, 8000.0, 11000.0],
        max_drawdown=20.0,
        closed_trades=2,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    # max_dd_dollars = 20% of 10000 = 2000
    # recovery = 1000 / 2000 = 0.5
    assert report.recovery_factor == 0.5


# ── CANCEL trades excluded ──────────────────────────────────────────────────


def test_cancelled_trades_excluded(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="CANCEL", pnl=0.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t1.id, quantity=1.0, pnl=0.0, status=CANCEL,
    )

    snap = PortfolioSnapshot(
        total_equity=10000.0,
        initial_capital=10000.0,
        total_pnl=0.0,
        equity_curve=[10000.0],
        max_drawdown=0.0,
        closed_trades=0,
    )

    engine = PerformanceEngine(session_factory=session_factory)
    report = engine.report(snap)

    assert report.sharpe_ratio == 0.0
    assert report.average_win == 0.0
    assert report.consecutive_wins == 0


# ── Integration with PortfolioEngine ────────────────────────────────────────


def test_integration_with_portfolio(db_session, session_factory):
    now = datetime.now(timezone.utc)
    t1 = _make_trade(
        db_session, signal_id=1, status="TP_HIT", pnl=2000.0,
        created_at=now - timedelta(hours=24), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t1.id, quantity=1.0, pnl=2000.0, status=TAKE_PROFIT,
    )
    t2 = _make_trade(
        db_session, signal_id=2, status="SL_HIT", pnl=-500.0,
        created_at=now - timedelta(hours=12), closed_at=now,
    )
    _make_paper_trade(
        db_session, position_id=t2.id, quantity=1.0, pnl=-500.0, status=STOP_LOSS,
    )

    # Generate snapshot from PortfolioEngine
    from portfolio import PortfolioEngine
    pe = PortfolioEngine(session_factory=session_factory, initial_capital=10000.0)
    snap = pe.snapshot()

    perf_engine = PerformanceEngine(session_factory=session_factory)
    report = perf_engine.report(snap)

    assert report.average_win == 2000.0
    assert report.average_loss == -500.0
    assert report.expectancy == 750.0  # 0.5*2000 - 0.5*500 = 750
    assert report.payoff_ratio == 4.0  # 2000 / 500
    assert report.largest_win == 2000.0
    assert report.largest_loss == -500.0
    assert report.consecutive_wins == 1
    assert report.consecutive_losses == 1
    assert report.sharpe_ratio != 0.0
    assert report.sortino_ratio != 0.0
