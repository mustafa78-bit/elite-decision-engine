"""Tests for simulator/simulator_engine.py's open/close cash-flow formulas.

Covers 4 related bugs found in the same code path
(SPRINT_JULES_SIMULATOR_CASH_ACCOUNTING_BUG.md):

  A. execute_manual_trade() never deducted cash on open at all.
  B. _close_trade()'s cash settlement used a dead ternary (both branches
     identical), so a SHORT's cash effect moved the same direction as a
     LONG's -- inverted relative to the SHORT's own recorded net_pnl.
  C. The entry fee was computed (trade.fees) and correctly subtracted from
     net_pnl, but never actually left state.cash.
  D. _execute_ai_trade()'s open-side debit used the raw pre-slippage price
     instead of the trade's actual (post-slippage) fill price.

The fix keeps a debit-at-open convention for BOTH sides (matching
_process_candle()'s already-correct unrealized mark-to-market formula,
which assumes this same convention) and makes the CLOSE-side settlement
side-aware: LONG credits quantity*exit_price back, SHORT credits
quantity*(2*entry_price - exit_price) -- the same expression
_process_candle() already uses for an OPEN SHORT's unrealized contribution,
so cash and portfolio_value stay consistent both mid-trade and at close.

Every test's core assertion: the net change in state.cash across a full
open+close cycle must exactly equal the trade's own recorded net_pnl
(trade.pnl), which already correctly accounts for both fee legs and side.
"""

from __future__ import annotations

import pytest

from simulator.models import SimulatedCandle, SimulatedDecision, SimulatorConfig, SimulatorState
from simulator.simulator_engine import SimulatorEngine


def _make_engine_with_state(portfolio_value: float = 150.0, cash: float = 100_000.0) -> SimulatorEngine:
    engine = SimulatorEngine()
    engine._state = SimulatorState(
        session_id="s1",
        config=SimulatorConfig(fee_rate=0.001, slippage_bps=0, risk_per_trade=0.02),
        cash=cash,
        portfolio_value=portfolio_value,
    )
    return engine


class TestManualTradeCashAccounting:
    def test_manual_long_open_close_cash_matches_net_pnl(self):
        engine = _make_engine_with_state()
        cash_before = engine._state.cash

        trade = engine.execute_manual_trade(
            side="LONG", entry_price=100.0, stop_loss=90.0, take_profit=120.0, quantity=1.0,
        )
        engine.close_trade(trade.id, exit_price=110.0)

        cash_after = engine._state.cash
        assert (cash_after - cash_before) == pytest.approx(trade.pnl, abs=1e-6)

    def test_manual_short_open_close_cash_matches_net_pnl(self):
        # The exact worked example from the sprint doc: entry=100, qty=1,
        # fee_rate=0.001, exit=90 -- gross_pnl=+10, fees=0.10+0.09=0.19,
        # net_pnl=+9.81. Under the old dead-ternary code this produced a
        # cash change of -10.09 for a trade recorded as a +9.81 win.
        engine = _make_engine_with_state()
        cash_before = engine._state.cash

        trade = engine.execute_manual_trade(
            side="SHORT", entry_price=100.0, stop_loss=110.0, take_profit=80.0, quantity=1.0,
        )
        engine.close_trade(trade.id, exit_price=90.0)

        cash_after = engine._state.cash
        assert trade.pnl == 9.81
        assert (cash_after - cash_before) == pytest.approx(trade.pnl, abs=1e-6)

    def test_manual_trade_deducts_cash_immediately_on_open(self):
        # Bug A: execute_manual_trade() previously never touched state.cash
        # at all until close.
        engine = _make_engine_with_state()
        cash_before = engine._state.cash

        trade = engine.execute_manual_trade(
            side="LONG", entry_price=100.0, stop_loss=90.0, take_profit=120.0, quantity=1.0,
        )

        # entry fee = 1 * 100 * 0.001 = 0.10; open debit = 100 + 0.10 = 100.10
        assert engine._state.cash == pytest.approx(cash_before - 100.10, abs=1e-6)
        assert trade.status == "OPEN"


class TestAiTradeCashAccounting:
    def _make_decision(self, side: str) -> SimulatedDecision:
        return SimulatedDecision(
            id="dec-1", symbol="BTC", side=side, timestamp=0, price=100.0,
            decision="BUY" if side == "LONG" else "SELL",
            confidence=80.0, evidence_strength=70.0, risk_score=20.0,
        )

    def test_ai_long_open_close_cash_matches_net_pnl(self):
        engine = _make_engine_with_state()
        cash_before = engine._state.cash
        candle = SimulatedCandle(timestamp=0, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0)

        engine._execute_ai_trade("LONG", candle, self._make_decision("LONG"))
        trade = engine._state.trades[0]
        engine._close_trade(trade, exit_price=110.0, reason="TAKE_PROFIT")

        cash_after = engine._state.cash
        assert (cash_after - cash_before) == pytest.approx(trade.pnl, abs=1e-6)

    def test_ai_short_open_close_cash_matches_net_pnl(self):
        engine = _make_engine_with_state()
        cash_before = engine._state.cash
        candle = SimulatedCandle(timestamp=0, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0)

        engine._execute_ai_trade("SHORT", candle, self._make_decision("SHORT"))
        trade = engine._state.trades[0]
        engine._close_trade(trade, exit_price=90.0, reason="TAKE_PROFIT")

        cash_after = engine._state.cash
        assert (cash_after - cash_before) == pytest.approx(trade.pnl, abs=1e-6)

    def test_ai_trade_open_debit_uses_post_slippage_fill_price(self):
        # Bug D: the open-side debit previously used candle.close (the raw
        # pre-slippage price) instead of trade.entry_price (the actual
        # fill price _create_trade() computed and stored).
        engine = _make_engine_with_state()
        engine._state.config.slippage_bps = 50  # 0.5%, large enough to be unmistakable
        cash_before = engine._state.cash
        candle = SimulatedCandle(timestamp=0, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0)

        engine._execute_ai_trade("LONG", candle, self._make_decision("LONG"))
        trade = engine._state.trades[0]

        # LONG fill price is slipped UP from 100 -- confirm the debit used
        # that higher price, not the raw 100.
        assert trade.entry_price > 100.0
        expected_debit = trade.quantity * trade.entry_price + trade.fees
        assert (cash_before - engine._state.cash) == pytest.approx(expected_debit, abs=1e-6)


class TestMonitorOpenTradesRoutesThroughSameCloseLogic:
    def test_tp_hit_via_monitor_uses_the_fixed_cash_formula(self):
        # Confirms _monitor_open_trades()'s TP/SL-triggered close path routes
        # through the same _close_trade() fixed above -- no separate fix
        # needed there.
        engine = _make_engine_with_state()
        cash_before_open = engine._state.cash
        trade = engine.execute_manual_trade(
            side="SHORT", entry_price=100.0, stop_loss=110.0, take_profit=90.0, quantity=1.0,
        )

        hit_candle = SimulatedCandle(timestamp=1, open=95.0, high=96.0, low=89.0, close=90.0, volume=1.0)
        engine._monitor_open_trades(hit_candle)

        assert trade.status == "CLOSED"
        assert trade.close_reason == "TAKE_PROFIT"
        assert (engine._state.cash - cash_before_open) == pytest.approx(trade.pnl, abs=1e-6)
