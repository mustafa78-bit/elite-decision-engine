"""Tests proving that PerformanceEngine correctly handles unit mismatch and mixed quantities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from database import (
    PaperTrade,
    Trade,
)
from performance_engine import PerformanceEngine


def _make_trade(db_session, **overrides):
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        entry=90000.0,
        stop=89000.0,
        tp1=91000.0,
        status="CLOSED",
        pnl=500.0,
        created_at=datetime.now(UTC) - timedelta(hours=2),
        closed_at=datetime.now(UTC),
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
        entry=90000.0,
        quantity=0.05,
        pnl=25.0,
        status="CLOSED",
    )
    kwargs.update(overrides)
    pt = PaperTrade(**kwargs)
    db_session.add(pt)
    db_session.flush()
    return pt


def test_performance_engine_unit_mismatch(db_session, session_factory):
    # Trade 1: BTC trade. Raw per-unit PnL = 500.0. Quantity = 0.05. Real dollar PnL = 25.0.
    t1 = _make_trade(
        db_session,
        symbol="BTCUSDT",
        side="LONG",
        entry=90000.0,
        stop=88000.0,  # risk = 2000.0 -> R multiple = 500 / 2000 = 0.25 R
        pnl=500.0,
        status="CLOSED",
    )
    _make_paper_trade(
        db_session,
        position_id=t1.id,
        symbol="BTCUSDT",
        side="LONG",
        quantity=0.05,
        pnl=25.0,
        status="CLOSED",
    )

    # Trade 2: ETH trade. Raw per-unit PnL = -50.0. Quantity = 2.0. Real dollar PnL = -100.0.
    t2 = _make_trade(
        db_session,
        symbol="ETHUSDT",
        side="LONG",
        entry=3000.0,
        stop=2800.0,  # risk = 200.0 -> R multiple = -50 / 200 = -0.25 R
        pnl=-50.0,
        status="CLOSED",
    )
    _make_paper_trade(
        db_session,
        position_id=t2.id,
        symbol="ETHUSDT",
        side="LONG",
        quantity=2.0,
        pnl=-100.0,
        status="CLOSED",
    )

    # Instantiate root-level PerformanceEngine
    # We set initial_equity to 10000.0
    engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000.0)
    stats = engine.stats()

    # --- Verification of dollar-denominated statistics ---
    # Real dollar pnls list = [25.0, -100.0]
    # gross_profit = 25.0
    # gross_loss = 100.0
    # profit_factor = 25.0 / 100.0 = 0.25
    assert stats.profit_factor == 0.25

    # expectancy: win_rate = 0.5, loss_rate = 0.5, avg_win = 25.0, avg_loss = -100.0
    # expectancy = 0.5 * 25.0 - 0.5 * 100.0 = -37.5
    assert stats.expectancy == -37.5

    # best_trade & worst_trade
    assert stats.best_trade == 25.0
    assert stats.worst_trade == -100.0

    # recovery_factor: total_pnl = -75.0.
    # peak_pnl = 25.0 (after trade 1). cum_pnl sequence: 0.0 -> 25.0 -> -75.0
    # max_dd_dollars = peak_pnl - (-75.0) = 100.0
    # recovery = total_pnl / max_dd_dollars = -75.0 / 100.0 = -0.75
    assert stats.recovery_factor == -0.75

    # calmar_ratio: total_return_pct = -75.0 / 10000.0 * 100 = -0.75%
    # cum_eq: 10000.0 -> 10025.0 -> 9925.0
    # peak_eq = 10025.0
    # max_dd_pct = (10025.0 - 9925.0) / 10025.0 = 100.0 / 10025.0 = 0.009975062 (approx 0.9975%)
    # calmar_ratio = -0.75 / (max_dd_pct * 100) = -0.75 / 0.9975062 = -0.7519
    expected_max_dd_pct = 100.0 / 10025.0
    expected_calmar = -0.75 / (expected_max_dd_pct * 100)
    assert abs(stats.calmar_ratio - expected_calmar) < 1e-4

    # --- Verification of ratio-based quantity-independent metrics ---
    # average_r_multiple: t1 = 500 / 2000 = 0.25, t2 = -50 / 200 = -0.25
    # average_r_multiple = (0.25 + -0.25) / 2 = 0.0
    assert stats.average_r_multiple == 0.0


def test_performance_engine_no_paper_trade_fallback(db_session, session_factory):
    # Test that when no matching PaperTrade exists, we fallback to raw trade.pnl (equivalent to qty=1.0)
    _make_trade(
        db_session,
        symbol="BTCUSDT",
        side="LONG",
        entry=90000.0,
        stop=88000.0,
        pnl=500.0,
        status="CLOSED",
    )
    # NO PaperTrade created for this trade

    engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000.0)
    stats = engine.stats()

    # With only 1 trade having raw pnl=500.0 and no PaperTrade, it should use fallback pnl=500.0
    assert stats.best_trade == 500.0
    assert stats.worst_trade == 500.0
    assert stats.expectancy == 500.0
    assert stats.profit_factor == 999.99  # no loss fallback
