"""Unit tests for TP/SL calculation logic."""

from execution.tp_sl import TPSLEngine


class TestTPSLEngine:

    def test_long_calculation(self):
        result = TPSLEngine().calculate(entry=50000.0, atr=500.0, side="LONG")

        assert result["entry"] == 50000.0
        assert result["stop"] == 49250.0
        assert result["tp1"] == 51000.0
        assert result["tp2"] == 52000.0

    def test_short_calculation(self):
        result = TPSLEngine().calculate(entry=50000.0, atr=500.0, side="SHORT")

        assert result["entry"] == 50000.0
        assert result["stop"] == 50750.0
        assert result["tp1"] == 49000.0
        assert result["tp2"] == 48000.0

    def test_risk_reward_ratio(self):
        long_rr = TPSLEngine().calculate(entry=50000.0, atr=500.0, side="LONG")["rr"]
        short_rr = TPSLEngine().calculate(entry=50000.0, atr=500.0, side="SHORT")["rr"]

        assert abs(long_rr - 1.33) < 0.01
        assert abs(short_rr - 1.33) < 0.01

    def test_zero_atr_fallback(self):
        result = TPSLEngine().calculate(entry=50000.0, atr=0.0, side="LONG")

        assert result["stop"] == 49250.0
        assert result["tp1"] == 51000.0

    def test_negative_atr_fallback(self):
        result = TPSLEngine().calculate(entry=50000.0, atr=-1.0, side="LONG")

        assert result["stop"] == 49250.0

    def test_case_insensitive_side(self):
        long_a = TPSLEngine().calculate(entry=50000.0, atr=500.0, side="long")
        long_b = TPSLEngine().calculate(entry=50000.0, atr=500.0, side="Long")

        assert long_a["stop"] == 49250.0
        assert long_a == long_b

    def test_zero_entry_raises(self):
        import pytest
        with pytest.raises(ValueError, match="entry=0"):
            TPSLEngine().calculate(entry=0.0, atr=500.0, side="LONG")

    def test_none_entry_raises(self):
        import pytest
        with pytest.raises(ValueError, match="entry=None"):
            TPSLEngine().calculate(entry=None, atr=500.0, side="LONG")
