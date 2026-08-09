"""Tests for RiskEngine scoring and evaluation."""

import pytest

from scoring.risk_engine import RiskEngine


class TestRiskEngineScore:

    def setup_method(self):
        self.engine = RiskEngine()

    def test_score_default_returns_one(self):
        result = self.engine.score({"atr": 0}, {"score": 0})
        assert result == 1.0

    def test_score_volatility_reduces_score(self):
        result = self.engine.score({"atr": 0}, {"score": 1.0})
        assert result < 1.0
        assert result >= 0.0

    def test_score_atr_extreme_reduces_score(self):
        # atr=3000 @ price=20000 -> 15% ATR/price, above the 10% extreme tier
        result = self.engine.score({"atr": 3000}, {"score": 0}, price=20000)
        assert result < 1.0
        assert result == pytest.approx(0.80, abs=0.01)

    def test_score_atr_high_reduces_score(self):
        # atr=2000 @ price=25000 -> 8% ATR/price, in the 6-10% high tier
        result = self.engine.score({"atr": 2000}, {"score": 0}, price=25000)
        assert result == pytest.approx(0.90, abs=0.01)

    def test_score_atr_moderate_reduces_score(self):
        # atr=1000 @ price=20000 -> 5% ATR/price, in the 3-6% moderate tier
        result = self.engine.score({"atr": 1000}, {"score": 0}, price=20000)
        assert result == pytest.approx(0.95, abs=0.01)

    def test_score_clamps_to_zero(self):
        result = self.engine.score({"atr": 3000}, {"score": 2.0}, price=20000)
        assert result >= 0.0
        assert result <= 1.0

    def test_score_rounds_to_two_decimals(self):
        result = self.engine.score({"atr": 700}, {"score": 0.5}, price=20000)
        assert isinstance(result, float)
        assert len(str(result).split(".")[1]) <= 2

    def test_score_no_price_applies_no_atr_penalty(self):
        # price=0 (the default) can't normalize ATR into a percentage --
        # matches the "no price available" real-world case, not an extreme
        # reading by omission.
        result = self.engine.score({"atr": 3000}, {"score": 0})
        assert result == 1.0

    def test_score_low_price_high_relative_volatility_is_penalized(self):
        # DOGE-style: atr=0.02, price=0.15 -> ~13.3% ATR/price, genuinely
        # extreme relative volatility despite a tiny absolute ATR that the
        # old raw-dollar thresholds (700/1500/2500) would never have flagged.
        result = self.engine.score({"atr": 0.02}, {"score": 0}, price=0.15)
        assert result == pytest.approx(0.80, abs=0.01)

    def test_score_high_price_low_relative_volatility_is_not_penalized(self):
        # BTC-style: atr=800, price=65000 -> ~1.2% ATR/price, genuinely calm
        # relative volatility despite an absolute ATR the old thresholds
        # would have penalized (atr > 700 -> "moderate").
        result = self.engine.score({"atr": 800}, {"score": 0}, price=65000)
        assert result == 1.0


class TestRiskEngineEvaluate:

    def setup_method(self):
        self.engine = RiskEngine()

    def test_evaluate_returns_dict(self):
        result = self.engine.evaluate({"atr": 0}, {"score": 0})
        assert isinstance(result, dict)
        assert "risk_score" in result
        assert "penalties" in result
        assert "atr" in result
        assert "atr_pct" in result
        assert "volatility_score" in result

    def test_evaluate_risk_score_matches_score_method(self):
        score_result = self.engine.score({"atr": 1500}, {"score": 0.5}, price=20000)
        eval_result = self.engine.evaluate({"atr": 1500}, {"score": 0.5}, price=20000)
        assert eval_result["risk_score"] == score_result

    def test_evaluate_penalties_includes_volatility(self):
        result = self.engine.evaluate({"atr": 0}, {"score": 1.0})
        assert "volatility" in result["penalties"]

    def test_evaluate_penalties_includes_atr(self):
        result = self.engine.evaluate({"atr": 3000}, {"score": 0}, price=20000)
        assert len(result["penalties"]) > 0

    def test_evaluate_no_penalties_when_no_risk(self):
        result = self.engine.evaluate({"atr": 0}, {"score": 0})
        assert result["penalties"] == {}
        assert result["risk_score"] == 1.0

    def test_evaluate_backward_compat_score_still_works(self):
        assert self.engine.score({"atr": 1000}, {"score": 0}, price=20000) == 0.95
