"""Tests for trailing-stop support in simulator/simulator_engine.py.

trailing_stop was accepted from the user, stored on SimulatedTrade, and
displayed in the UI, but _monitor_open_trades() (the only place that
evaluates whether an open trade should close) never read it -- a trade with
a trailing stop set behaved identically to one without.
(SPRINT_JULES_SIMULATOR_TRAILING_STOP_NEVER_IMPLEMENTED.md)

trailing_stop is an absolute price distance (matching stop_loss/take_profit,
which are already absolute price levels, not percentages -- confirmed via
frontend/src/pages/MarketSimulator.tsx's manual-trade form, where all three
inputs share the same styling/convention with no percent sign).
"""

from __future__ import annotations

import pytest

from simulator.models import SimulatedCandle, SimulatorConfig, SimulatorState
from simulator.simulator_engine import SimulatorEngine


def _make_engine_with_state(cash: float = 100_000.0) -> SimulatorEngine:
    engine = SimulatorEngine()
    engine._state = SimulatorState(
        session_id="s1",
        config=SimulatorConfig(fee_rate=0.0, slippage_bps=0, risk_per_trade=0.02),
        cash=cash,
        portfolio_value=cash,
    )
    return engine


class TestTrailingStopLong:
    def test_ratchets_up_and_closes_at_ratcheted_level_not_fixed_stop(self):
        engine = _make_engine_with_state()
        trade = engine.execute_manual_trade(
            side="LONG", entry_price=100.0, stop_loss=80.0, take_profit=200.0,
            quantity=1.0, trailing_stop=5.0,
        )

        # Price rises to a new peak of 120; low stays well above the new
        # trailing level (120 - 5 = 115), so the trade must stay open.
        rise_candle = SimulatedCandle(timestamp=1, open=100.0, high=120.0, low=118.0, close=119.0, volume=1.0)
        engine._monitor_open_trades(rise_candle)
        assert trade.status == "OPEN"
        assert trade.trailing_stop_peak == 120.0

        # Price pulls back. It never gets anywhere near the original fixed
        # stop_loss (80), but does cross the ratcheted trailing level (115).
        pullback_candle = SimulatedCandle(timestamp=2, open=119.0, high=119.0, low=112.0, close=114.0, volume=1.0)
        engine._monitor_open_trades(pullback_candle)

        assert trade.status == "CLOSED"
        assert trade.close_reason == "TRAILING_STOP"
        assert trade.exit_price == 115.0

    def test_never_ratchets_down_on_a_pullback_that_does_not_trigger(self):
        engine = _make_engine_with_state()
        trade = engine.execute_manual_trade(
            side="LONG", entry_price=100.0, stop_loss=50.0, take_profit=200.0,
            quantity=1.0, trailing_stop=20.0,
        )

        up_candle = SimulatedCandle(timestamp=1, open=100.0, high=150.0, low=140.0, close=145.0, volume=1.0)
        engine._monitor_open_trades(up_candle)
        assert trade.trailing_stop_peak == 150.0

        # A mild pullback that doesn't cross 150-20=130 must not lower the
        # tracked peak, even though price is now off its high.
        small_pullback = SimulatedCandle(timestamp=2, open=145.0, high=146.0, low=135.0, close=140.0, volume=1.0)
        engine._monitor_open_trades(small_pullback)
        assert trade.status == "OPEN"
        assert trade.trailing_stop_peak == 150.0


class TestTrailingStopShort:
    def test_ratchets_down_and_closes_at_ratcheted_level_not_fixed_stop(self):
        engine = _make_engine_with_state()
        trade = engine.execute_manual_trade(
            side="SHORT", entry_price=100.0, stop_loss=120.0, take_profit=0.0,
            quantity=1.0, trailing_stop=5.0,
        )

        # Price falls to a new trough of 80; high stays well below the new
        # trailing level (80 + 5 = 85), so the trade must stay open.
        fall_candle = SimulatedCandle(timestamp=1, open=100.0, high=82.0, low=80.0, close=81.0, volume=1.0)
        engine._monitor_open_trades(fall_candle)
        assert trade.status == "OPEN"
        assert trade.trailing_stop_peak == 80.0

        # Price bounces back up. It never gets anywhere near the original
        # fixed stop_loss (120), but does cross the ratcheted trailing
        # level (85).
        bounce_candle = SimulatedCandle(timestamp=2, open=81.0, high=90.0, low=81.0, close=88.0, volume=1.0)
        engine._monitor_open_trades(bounce_candle)

        assert trade.status == "CLOSED"
        assert trade.close_reason == "TRAILING_STOP"
        assert trade.exit_price == 85.0


class TestTrailingStopCoexistsWithFixedStop:
    def test_fixed_stop_loss_wins_when_tighter_than_trailing_level(self):
        engine = _make_engine_with_state()
        # Trailing level after the rise would be 120-5=115, but the fixed
        # stop_loss (118) is tighter (higher) -- it should govern instead.
        trade = engine.execute_manual_trade(
            side="LONG", entry_price=100.0, stop_loss=118.0, take_profit=200.0,
            quantity=1.0, trailing_stop=5.0,
        )
        rise_candle = SimulatedCandle(timestamp=1, open=100.0, high=120.0, low=119.0, close=119.5, volume=1.0)
        engine._monitor_open_trades(rise_candle)
        assert trade.status == "OPEN"

        drop_candle = SimulatedCandle(timestamp=2, open=119.5, high=119.5, low=117.0, close=118.0, volume=1.0)
        engine._monitor_open_trades(drop_candle)
        assert trade.status == "CLOSED"
        assert trade.close_reason == "STOP_LOSS"
        assert trade.exit_price == 118.0


class TestNoTrailingStopUnaffected:
    def test_trade_without_trailing_stop_only_evaluates_fixed_stop_loss(self):
        engine = _make_engine_with_state()
        trade = engine.execute_manual_trade(
            side="LONG", entry_price=100.0, stop_loss=90.0, take_profit=200.0, quantity=1.0,
        )
        candle = SimulatedCandle(timestamp=1, open=100.0, high=150.0, low=140.0, close=145.0, volume=1.0)
        engine._monitor_open_trades(candle)
        assert trade.status == "OPEN"
        assert trade.trailing_stop_peak is None
