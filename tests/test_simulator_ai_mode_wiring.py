"""Tests that FULL_AI mode -- the SimulatorConfig default -- actually reaches a
real council and can place a real trade, instead of silently defaulting to
HOLD forever on every candle
(SPRINT_JULES_SIMULATOR_AI_MODE_NEVER_TRADES_IN_PRODUCTION.md).

Covers both halves of the original bug:
1. The production engine construction (`api/routes/simulator.py::_get_engine()`)
   never passed a real `council_engine` at all.
2. Even if wired, the signal handed to the council was a hardcoded mock with
   every score fixed at 0.5 -- `_build_scores_from_replay()` now computes
   real indicator/volume/risk scores from the replayed candle history.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pandas as pd
import pytest

import api.routes.simulator as simulator_routes
from council.consensus import ConsensusEngine
from simulator.models import AIDecisionMode, SimSpeed, SimulatorConfig
from simulator.replay_engine import MarketReplayEngine
from simulator.simulator_engine import SimulatorEngine


def _make_deterministic_uptrend_df(num_candles: int = 260, start_price: float = 30000.0) -> pd.DataFrame:
    # A clean, noise-free 1%-per-candle uptrend -- deliberately deterministic
    # (unlike simulator/scenarios.py's RNG-based scenarios) so the resulting
    # AI decision assertions aren't flaky.
    now = int(datetime.now(UTC).timestamp() * 1000)
    rows = []
    price = start_price
    for i in range(num_candles):
        prev = price
        price *= 1.01
        rows.append({
            "timestamp": now - (num_candles - i) * 3_600_000,
            "open": prev,
            "high": price * 1.002,
            "low": prev * 0.998,
            "close": price,
            "volume": 5000.0,
        })
    return pd.DataFrame(rows)


class _DeterministicUptrendReplayEngine(MarketReplayEngine):
    """Same production replay engine, with only the synthetic-data seam
    swapped for a deterministic uptrend instead of a random walk."""

    def _generate_synthetic(self, symbol, timeframe, start_date, end_date):
        return _make_deterministic_uptrend_df()


class TestProductionEngineWiring:
    def test_get_engine_wires_a_real_council_with_agents_registered(self):
        simulator_routes._engine = None
        try:
            engine = simulator_routes._get_engine()
            assert engine._council is not None
            assert len(engine._council.agents) > 0
        finally:
            simulator_routes._engine = None


class TestAIModeActuallyTrades:
    @pytest.mark.asyncio
    async def test_full_ai_mode_produces_a_real_buy_decision_under_a_clean_uptrend(self):
        council = ConsensusEngine()
        council.register_defaults()
        engine = SimulatorEngine(
            replay_engine=_DeterministicUptrendReplayEngine(),
            council_engine=council,
        )
        config = SimulatorConfig(
            symbol="BTC",
            timeframe="1h",
            ai_mode=AIDecisionMode.FULL_AI,
            speed=SimSpeed.UNLIMITED,
        )

        await engine.start(config)
        try:
            await engine._task
        except asyncio.CancelledError:
            pass

        decisions = engine._state.decisions
        assert len(decisions) > 0
        assert any(d.decision == "BUY" for d in decisions)

        # Real data flowed through, not the old hardcoded 0.5-everything mock:
        # the Technical agent's real EMA/RSI readings should show up in the
        # council report, distinctly different from the flat 0.5 placeholder.
        buy_decision = next(d for d in decisions if d.decision == "BUY")
        technical_report = next(
            r for r in buy_decision.agent_reports if r["agent_name"] == "Technical"
        )
        assert technical_report["data_points"]["ema20"] != 0.5
        assert technical_report["data_points"]["rsi"] != 50

    @pytest.mark.asyncio
    async def test_ai_mode_places_a_real_trade_not_just_a_decision(self):
        council = ConsensusEngine()
        council.register_defaults()
        engine = SimulatorEngine(
            replay_engine=_DeterministicUptrendReplayEngine(),
            council_engine=council,
        )
        config = SimulatorConfig(
            symbol="BTC",
            timeframe="1h",
            ai_mode=AIDecisionMode.FULL_AI,
            speed=SimSpeed.UNLIMITED,
        )

        await engine.start(config)
        try:
            await engine._task
        except asyncio.CancelledError:
            pass

        assert len(engine._state.trades) > 0
        assert any(t.side == "LONG" for t in engine._state.trades)
