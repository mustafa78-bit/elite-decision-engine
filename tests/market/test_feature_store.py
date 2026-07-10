"""Tests for FeatureStore."""

from market.features import FeatureStore


class TestFeatureStore:

    def setup_method(self):
        self.store = FeatureStore()

    def test_empty_indicators(self):
        features = self.store.extract({})
        assert features["trend"] == "UNKNOWN"
        assert features["momentum"] == "UNKNOWN"

    def test_bullish_trend_long(self):
        features = self.store.extract({
            "ema20": 110, "ema50": 105, "ema200": 100,
            "rsi": 60, "atr": 500, "volatility_score": 0.3, "volume_score": 0.8,
        }, side="LONG")
        assert features["trend"] == "BULLISH"
        assert features["momentum"] == "STRONG"
        assert features["liquidity"] == "HIGH"

    def test_bearish_trend_long(self):
        features = self.store.extract({
            "ema20": 90, "ema50": 95, "ema200": 100,
            "rsi": 35, "atr": 500, "volatility_score": 0.3, "volume_score": 0.5,
        }, side="LONG")
        assert features["trend"] == "BEARISH"
        assert features["momentum"] == "WEAK"

    def test_high_risk(self):
        features = self.store.extract({
            "ema20": 100, "ema50": 100, "ema200": 100,
            "rsi": 50, "atr": 3000, "volatility_score": 0.8, "volume_score": 0.5,
        })
        assert features["risk"] == "HIGH"

    def test_low_risk(self):
        features = self.store.extract({
            "ema20": 100, "ema50": 100, "ema200": 100,
            "rsi": 50, "atr": 300, "volatility_score": 0.2, "volume_score": 0.5,
        })
        assert features["risk"] == "LOW"

    def test_volatility_classification(self):
        features = self.store.extract({
            "ema20": 100, "ema50": 100, "ema200": 100,
            "rsi": 50, "atr": 200, "volatility_score": 0.3, "volume_score": 0.5,
            "entry": 50000,
        })
        assert features["volatility_class"] == "LOW"

        features2 = self.store.extract({
            "ema20": 100, "ema50": 100, "ema200": 100,
            "rsi": 50, "atr": 3000, "volatility_score": 0.3, "volume_score": 0.5,
            "entry": 50000,
        })
        assert features2["volatility_class"] == "EXTREME"

    def test_regime_score(self):
        features = self.store.extract({
            "ema20": 110, "ema50": 105, "ema200": 100,
            "rsi": 60, "atr": 300, "volatility_score": 0.2, "volume_score": 0.8,
        })
        assert 0.0 <= features["regime_score"] <= 1.0
        assert features["regime_score"] > 0.5

    def test_momentum_overbought(self):
        features = self.store.extract({
            "ema20": 100, "ema50": 100, "ema200": 100,
            "rsi": 80, "atr": 500, "volatility_score": 0.3, "volume_score": 0.5,
        })
        assert features["momentum"] == "OVERBOUGHT"

    def test_momentum_oversold(self):
        features = self.store.extract({
            "ema20": 100, "ema50": 100, "ema200": 100,
            "rsi": 20, "atr": 500, "volatility_score": 0.3, "volume_score": 0.5,
        })
        assert features["momentum"] == "OVERSOLD"
