"""OHLC-invariant regression tests for the simulator's synthetic candle generators.

Both simulator/replay_engine.py::MarketReplayEngine._generate_synthetic() and
simulator/scenarios.py::generate_scenario_data() previously computed high/low
as a small perturbation of close alone, ignoring open -- whenever a candle's
return was large enough, open ended up outside [low, high], producing an
invalid candle. Since api/routes/simulator.py's _get_engine() never wires a
real data_provider, every simulation run in production used this broken
generator, and stop-loss/take-profit triggers in _monitor_open_trades() check
directly against candle.low/candle.high.

(SPRINT_JULES_SIMULATOR_SYNTHETIC_CANDLES_INVALID_OHLC.md)
"""

from __future__ import annotations

from simulator.models import ScenarioType
from simulator.replay_engine import MarketReplayEngine, synthesize_ohlc
from simulator.scenarios import generate_scenario_data


def _assert_valid_ohlc(df) -> None:
    assert len(df) > 0
    for row in df.itertuples():
        lo, hi, o, c = row.low, row.high, row.open, row.close
        assert lo <= min(o, c) <= max(o, c) <= hi, (
            f"invalid candle: open={o} close={c} high={hi} low={lo}"
        )


class TestSynthesizeOHLC:
    def test_bounds_hold_regardless_of_noise_and_direction(self):
        # open below close (up candle)
        high, low = synthesize_ohlc(100.0, 110.0, 0.01, 0.01)
        assert low <= min(100.0, 110.0) <= max(100.0, 110.0) <= high

        # open above close (down candle)
        high, low = synthesize_ohlc(110.0, 100.0, 0.01, 0.01)
        assert low <= min(100.0, 110.0) <= max(100.0, 110.0) <= high

        # zero noise -- bounds collapse exactly onto open/close
        high, low = synthesize_ohlc(100.0, 105.0, 0.0, 0.0)
        assert high == 105.0
        assert low == 100.0

        # large return -- open far from close, the exact case that broke
        # the old close-only formula
        high, low = synthesize_ohlc(100.0, 130.0, 0.001, 0.001)
        assert low <= 100.0 <= 130.0 <= high


class TestReplayEngineSyntheticCandles:
    def test_generated_candles_satisfy_ohlc_invariant(self):
        engine = MarketReplayEngine()
        df = engine._generate_synthetic(
            "BTCUSDT", "1h", start_date=None, end_date=None,
        )
        _assert_valid_ohlc(df)
        assert len(df) > 100


class TestScenarioSyntheticCandles:
    def test_all_scenario_types_satisfy_ohlc_invariant(self):
        for scenario_type in ScenarioType:
            df = generate_scenario_data(scenario_type, symbol="BTC", num_candles=200)
            _assert_valid_ohlc(df)
            assert len(df) == 200
