"""Tests for market regime AI."""

from scoring.regime_ai import RegimeAI


class TestRegimeAI:
    def test_empty_values(self):
        ai = RegimeAI()
        result = ai.detect({})
        assert result["regime"] == "UNKNOWN"
        assert result["trend"] == "NEUTRAL"

    def test_none_values(self):
        ai = RegimeAI()
        result = ai.detect(None)
        assert result["regime"] == "UNKNOWN"

    def test_bullish_trend(self):
        ai = RegimeAI()
        result = ai.detect({"ema20": 55000, "ema50": 54000, "ema200": 50000, "atr": 500, "close": 56000, "rsi": 65})
        assert result["regime"] == "TREND"
        assert result["trend"] == "BULLISH"

    def test_bearish_trend(self):
        ai = RegimeAI()
        result = ai.detect({"ema20": 45000, "ema50": 46000, "ema200": 50000, "atr": 500, "close": 44000, "rsi": 35})
        assert result["regime"] == "DOWNTREND"
        assert result["trend"] == "BEARISH"

    def test_dead_market(self):
        ai = RegimeAI()
        result = ai.detect({"ema20": 50000, "ema50": 50000, "ema200": 50000, "atr": 50, "close": 50000, "rsi": 50})
        assert result["regime"] == "DEAD"

    def test_range_market(self):
        ai = RegimeAI()
        result = ai.detect({"ema20": 51000, "ema50": 50500, "ema200": 52000, "atr": 300, "close": 50500, "rsi": 50})
        assert result["regime"] == "RANGE"

    def test_recovery_market(self):
        ai = RegimeAI()
        result = ai.detect({"ema20": 52000, "ema50": 48000, "ema200": 51000, "atr": 300, "close": 53000, "rsi": 55})
        assert result["regime"] == "RECOVERY"

    def test_volatility_classes(self):
        ai = RegimeAI()
        low_vol = ai.detect({"ema20": 50000, "ema50": 50000, "ema200": 50000, "atr": 200, "close": 50000, "rsi": 50})
        assert "volatility_class" in low_vol
        high_vol = ai.detect({"ema20": 50000, "ema50": 50000, "ema200": 50000, "atr": 5000, "close": 50000, "rsi": 50})
        assert high_vol["volatility_class"] == "EXTREME"

    def test_trend_strength(self):
        ai = RegimeAI()
        strong = ai.detect({"ema20": 55000, "ema50": 50000, "ema200": 45000, "atr": 500, "close": 56000, "rsi": 65})
        assert strong["trend_strength"] in ("STRONG", "MODERATE", "WEAK")

    def test_market_phase(self):
        ai = RegimeAI()
        result = ai.detect({"ema20": 55000, "ema50": 54000, "ema200": 50000, "atr": 500, "close": 56000, "rsi": 75})
        assert "market_phase" in result

    def test_score_range(self):
        ai = RegimeAI()
        for _ in range(10):
            result = ai.detect({"ema20": 50000, "ema50": 49500, "ema200": 49000, "atr": 400, "close": 50500, "rsi": 55})
            assert 0.0 <= result["score"] <= 1.0
