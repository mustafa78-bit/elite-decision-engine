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
            "ema20": 100000, "ema50": 100000, "ema200": 100000,
            "rsi": 50, "atr": 6000, "volatility_score": 0.8, "volume_score": 0.5,
        })
        # atr_pct = 6% (>5.0% adds 2) + vol_score (>0.7 adds 2) = 4 >= 3 -> HIGH
        assert features["risk"] == "HIGH"

    def test_low_risk(self):
        features = self.store.extract({
            "ema20": 100000, "ema50": 100000, "ema200": 100000,
            "rsi": 50, "atr": 300, "volatility_score": 0.2, "volume_score": 0.5,
        })
        # atr_pct = 0.3% (adds 0) + vol_score (adds 0) = 0 -> LOW
        assert features["risk"] == "LOW"

    def test_low_price_extreme_atr_percentage_high_risk(self):
        # DOGE-like low price ($0.15), extreme ATR percentage (0.02, which is ~13.3%)
        features = self.store.extract({
            "ema20": 0.15, "ema50": 0.15, "ema200": 0.15,
            "rsi": 50, "atr": 0.02, "volatility_score": 0.3, "volume_score": 0.5,
        })
        # atr_pct = 13.33% (> 5.0% adds 2) + vol_score 0.3 (adds 0) = 2 -> MEDIUM (not LOW!)
        assert features["risk"] == "MEDIUM"

    def test_high_price_low_atr_percentage_not_penalized(self):
        # Previously, an absolute ATR of 2000 would have triggered risk increments.
        # Now, with relative percentage, 2000 ATR on a 100000 price is 2%, which shouldn't penalize.
        features = self.store.extract({
            "ema20": 100000, "ema50": 100000, "ema200": 100000,
            "rsi": 50, "atr": 2000, "volatility_score": 0.3, "volume_score": 0.5,
        })
        # atr_pct = 2% (adds 0) + vol_score 0.3 (adds 0) = 0 -> LOW
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
