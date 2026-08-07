"""Tests that selecting a scenario actually changes what candles a simulation runs
against, instead of being silently ignored in favor of the generic synthetic
random walk (SPRINT_JULES_SIMULATOR_SCENARIO_SELECTION_DISCONNECTED.md)."""

import asyncio

import pytest

from simulator.models import ScenarioType, SimSpeed, SimulatorConfig
from simulator.simulator_engine import SimulatorEngine


async def _start_and_stop(config: SimulatorConfig) -> list:
    engine = SimulatorEngine()
    await engine.start(config)
    engine.stop()
    try:
        await engine._task
    except asyncio.CancelledError:
        pass
    return engine._replay.get_all()


class TestScenarioSelectionWiring:
    @pytest.mark.asyncio
    async def test_flash_crash_scenario_produces_its_characteristic_sharp_drop(self):
        config = SimulatorConfig(
            symbol="BTC",
            timeframe="1h",
            scenario=ScenarioType.FLASH_CRASH,
            speed=SimSpeed.UNLIMITED,
        )
        candles = await _start_and_stop(config)

        assert len(candles) > 0
        prices = [c.close for c in candles]
        peak, trough = max(prices), min(prices)
        # A flash crash should show a sharp peak-to-trough drawdown, unlike a
        # generic low-volatility random walk.
        assert (peak - trough) / peak > 0.10

    @pytest.mark.asyncio
    async def test_no_scenario_preserves_existing_default_fallback_behavior(self):
        config = SimulatorConfig(
            symbol="BTC",
            timeframe="1h",
            scenario=None,
            speed=SimSpeed.UNLIMITED,
        )
        candles = await _start_and_stop(config)

        # Default (no scenario) fallback is a ~30-day synthetic random walk at
        # 1h granularity (~720 candles), distinctly longer than any scenario's
        # short duration_candles (e.g. FLASH_CRASH's 50) -- proves the default
        # path is unaffected by the scenario wiring.
        assert len(candles) > 100
