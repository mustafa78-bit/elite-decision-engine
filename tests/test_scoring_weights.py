"""Tests for centralized scoring weights in config.py.

Verifies:
  - SCORE_WEIGHTS sum to 1.0
  - SCORE_WEIGHTS_PCT equals SCORE_WEIGHTS * 100
  - ScoringEngine uses SCORE_WEIGHTS from config
  - ConfidenceEngine uses SCORE_WEIGHTS_PCT from config
  - Weight changes propagate to engine outputs
"""

import pandas as pd
import pytest

from config import SCORE_WEIGHTS, SCORE_WEIGHTS_PCT
from core.confidence_engine import ConfidenceEngine
from scoring.scoring_engine import ScoringEngine


class TestConfigWeights:

    def test_weights_sum_to_one(self):
        assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 0.001

    def test_weights_pct_are_scaled(self):
        for key in SCORE_WEIGHTS:
            assert SCORE_WEIGHTS_PCT[key] == round(SCORE_WEIGHTS[key] * 100, 2)

    def test_weights_have_all_keys(self):
        expected_keys = {"trend", "volume", "btc", "mtf", "risk"}
        assert set(SCORE_WEIGHTS.keys()) == expected_keys
        assert set(SCORE_WEIGHTS_PCT.keys()) == expected_keys


class DummySignal:
    symbol = "BTCUSDT"
    side = "LONG"
    timeframe = "1h"


class TestConfidenceEngineUsesConfigWeights:

    def test_confidence_calculation_uses_config_weights(self, monkeypatch):
        overrides = {"trend": 0.40, "volume": 0.20, "btc": 0.15, "mtf": 0.15, "risk": 0.10}
        monkeypatch.setitem(SCORE_WEIGHTS, "trend", 0.40)
        monkeypatch.setitem(SCORE_WEIGHTS, "volume", 0.20)
        monkeypatch.setitem(SCORE_WEIGHTS, "btc", 0.15)
        monkeypatch.setitem(SCORE_WEIGHTS, "mtf", 0.15)
        monkeypatch.setitem(SCORE_WEIGHTS, "risk", 0.10)
        pct = {k: round(v * 100, 2) for k, v in overrides.items()}
        monkeypatch.setattr("core.confidence_engine.SCORE_WEIGHTS_PCT", pct)

        engine = ConfidenceEngine()
        scores = {
            "trend_score": 1.0,
            "volume_score": 1.0,
            "btc_score": 1.0,
            "mtf_score": 1.0,
            "risk_score": 0.5,
        }
        result = engine.calculate(scores)

        expected = 1.0 * 40 + 1.0 * 20 + 1.0 * 15 + 1.0 * 15 + 0.5 * 10
        assert result["confidence"] == expected

    def test_confidence_returns_known_values_for_default_weights(self):
        engine = ConfidenceEngine()
        scores = {
            "trend_score": 1.0,
            "volume_score": 1.0,
            "btc_score": 1.0,
            "mtf_score": 1.0,
            "risk_score": 1.0,
        }
        result = engine.calculate(scores)
        assert result["confidence"] == 100.0
        assert result["decision"] == "STRONG_APPROVE"

    def test_confidence_zero_inputs(self):
        engine = ConfidenceEngine()
        scores = {
            "trend_score": 0.0,
            "volume_score": 0.0,
            "btc_score": 0.0,
            "mtf_score": 0.0,
            "risk_score": 0.0,
        }
        result = engine.calculate(scores)
        assert result["confidence"] == 0.0
        assert result["decision"] == "REJECT"

    def test_confidence_clamps_at_100(self):
        engine = ConfidenceEngine()
        scores = {
            "trend_score": 2.0,
            "volume_score": 2.0,
            "btc_score": 2.0,
            "mtf_score": 2.0,
            "risk_score": 2.0,
        }
        result = engine.calculate(scores)
        assert result["confidence"] == 100.0


class TestScoringEngineUsesConfigWeights:

    def test_scoring_engine_uses_config_weights(self, monkeypatch):
        monkeypatch.setitem(SCORE_WEIGHTS, "trend", 0.50)
        monkeypatch.setitem(SCORE_WEIGHTS, "volume", 0.20)
        monkeypatch.setitem(SCORE_WEIGHTS, "btc", 0.10)
        monkeypatch.setitem(SCORE_WEIGHTS, "mtf", 0.10)
        monkeypatch.setitem(SCORE_WEIGHTS, "risk", 0.10)

        mock_df = _make_mock_df()
        monkeypatch.setattr(
            "scoring.scoring_engine.HyperliquidCollector.get_ohlcv",
            lambda _self, **kwargs: mock_df,
        )
        monkeypatch.setattr(
            "market_data.indicators.IndicatorEngine.calculate",
            lambda _self, df: {
                "ema20": 51000.0,
                "ema50": 50500.0,
                "ema200": 50200.0,
                "rsi": 55.0,
                "atr": 500.0,
            },
        )
        monkeypatch.setattr(
            "market_data.volume.VolumeEngine.score",
            lambda _self, df: {"score": 0.7},
        )
        monkeypatch.setattr(
            "market_data.btc_health.BTCHealth.score",
            lambda _self: 1.0,
        )
        monkeypatch.setattr(
            "market_data.volatility.VolatilityEngine.score",
            lambda _self, values: {"score": 0.6, "volatility": 0.01},
        )
        monkeypatch.setattr(
            "market_data.mtf.MTFEngine.score",
            lambda _self, symbol, side: 1.0,
        )
        monkeypatch.setattr(
            "scoring.risk_engine.RiskEngine.score",
            lambda _self, values, volatility: 0.5,
        )

        engine = ScoringEngine()
        result = engine.score(DummySignal())

        expected = (
            1.0 * 0.50 +
            0.7 * 0.20 +
            1.0 * 0.10 +
            1.0 * 0.10 +
            0.5 * 0.10
        )
        assert result["final_score"] == pytest.approx(expected, abs=0.001)

    def test_scoring_engine_error_return_preserved(self, monkeypatch):
        def _raise(*args, **kwargs):
            raise ValueError("test error")

        monkeypatch.setattr(
            "scoring.scoring_engine.HyperliquidCollector.get_ohlcv",
            _raise,
        )

        engine = ScoringEngine()
        result = engine.score(DummySignal())

        assert result["final_score"] == 0
        assert result["risk_score"] == 1


def _make_mock_df():
    n = 300
    base_price = 50000.0
    prices = [base_price + i * 10 for i in range(n)]
    return pd.DataFrame({
        "close": prices,
        "high": [p + 200 for p in prices],
        "low": [p - 200 for p in prices],
        "open": [p - 50 for p in prices],
        "volume": [1000.0 + (i % 10) * 100 for i in range(n)],
        "timestamp": [1700000000000 + i * 3600000 for i in range(n)],
    })
