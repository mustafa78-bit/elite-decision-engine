"""Tests for SimulatorEngine._process_candle()'s live mark-to-market equity valuation.

Verifies that unrealized PnL on OPEN positions is computed correctly for
both LONG and SHORT -- a prior bug used quantity*candle.close for both
sides, which is only correct for LONG and inverts the sign for SHORT.
"""

from simulator.models import SimulatedCandle, SimulatedTrade, SimulatorConfig, SimulatorState
from simulator.simulator_engine import SimulatorEngine


def _make_trade(**overrides) -> SimulatedTrade:
    # stop_loss/take_profit are set far outside any test candle's range so
    # _monitor_open_trades() never closes the position mid-test -- these
    # tests are specifically about the still-OPEN mark-to-market valuation.
    side = overrides.get("side", "LONG")
    kwargs = dict(
        id="t1",
        symbol="BTC",
        side=side,
        entry_price=50000.0,
        entry_time=0,
        quantity=0.1,
        leverage=1.0,
        stop_loss=1000.0 if side == "LONG" else 1_000_000.0,
        take_profit=1_000_000.0 if side == "LONG" else 1000.0,
        status="OPEN",
    )
    kwargs.update(overrides)
    return SimulatedTrade(**kwargs)


def _make_state(trade: SimulatedTrade, cash: float) -> SimulatorState:
    return SimulatorState(
        session_id="s1",
        config=SimulatorConfig(ai_mode="MANUAL"),
        cash=cash,
        trades=[trade],
        open_positions=1,
    )


def _candle(close: float) -> SimulatedCandle:
    return SimulatedCandle(timestamp=1000, open=close, high=close, low=close, close=close, volume=1.0)


class TestProcessCandleUnrealizedEquity:
    def test_long_position_gains_value_when_price_rises(self):
        # LONG opened at 50,000, qty 0.1 -> cash debited 5,000 at open.
        trade = _make_trade(side="LONG", entry_price=50000.0, quantity=0.1)
        state = _make_state(trade, cash=10000.0 - 5000.0)
        engine = SimulatorEngine()
        engine._state = state

        engine._process_candle(_candle(close=55000.0))

        # Real unrealized PnL: 0.1 * (55000 - 50000) = +500
        assert state.portfolio_value == 10000.0 + 500.0

    def test_short_position_gains_value_when_price_falls(self):
        # SHORT opened at 50,000, qty 0.1 -> cash debited 5,000 at open
        # (same unconditional debit as LONG, per _execute_ai_trade()).
        trade = _make_trade(side="SHORT", entry_price=50000.0, quantity=0.1)
        state = _make_state(trade, cash=10000.0 - 5000.0)
        engine = SimulatorEngine()
        engine._state = state

        engine._process_candle(_candle(close=45000.0))

        # Real unrealized PnL for a SHORT when price falls:
        # 0.1 * (50000 - 45000) = +500 -- a profitable move, portfolio_value
        # should INCREASE, not decrease.
        assert state.portfolio_value == 10000.0 + 500.0

    def test_short_position_loses_value_when_price_rises(self):
        trade = _make_trade(side="SHORT", entry_price=50000.0, quantity=0.1)
        state = _make_state(trade, cash=10000.0 - 5000.0)
        engine = SimulatorEngine()
        engine._state = state

        engine._process_candle(_candle(close=55000.0))

        # Real unrealized PnL for a SHORT when price rises:
        # 0.1 * (50000 - 55000) = -500 -- a losing move.
        assert state.portfolio_value == 10000.0 - 500.0

    def test_equity_curve_records_the_same_side_aware_value(self):
        trade = _make_trade(side="SHORT", entry_price=50000.0, quantity=0.1)
        state = _make_state(trade, cash=10000.0 - 5000.0)
        engine = SimulatorEngine()
        engine._state = state

        engine._process_candle(_candle(close=45000.0))

        assert state.equity_curve[-1]["value"] == round(10000.0 + 500.0, 2)
