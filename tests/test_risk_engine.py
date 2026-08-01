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
        result = self.engine.score({"atr": 3000}, {"score": 0})
        assert result < 1.0
        assert result == pytest.approx(0.80, abs=0.01)

    def test_score_atr_high_reduces_score(self):
        result = self.engine.score({"atr": 2000}, {"score": 0})
        assert result == pytest.approx(0.90, abs=0.01)

    def test_score_atr_moderate_reduces_score(self):
        result = self.engine.score({"atr": 1000}, {"score": 0})
        assert result == pytest.approx(0.95, abs=0.01)

    def test_score_clamps_to_zero(self):
        result = self.engine.score({"atr": 3000}, {"score": 2.0})
        assert result >= 0.0
        assert result <= 1.0

    def test_score_rounds_to_two_decimals(self):
        result = self.engine.score({"atr": 700}, {"score": 0.5})
        assert isinstance(result, float)
        assert len(str(result).split(".")[1]) <= 2


class TestRiskEngineEvaluate:

    def setup_method(self):
        self.engine = RiskEngine()

    def test_evaluate_returns_dict(self):
        result = self.engine.evaluate({"atr": 0}, {"score": 0})
        assert isinstance(result, dict)
        assert "risk_score" in result
        assert "penalties" in result
        assert "atr" in result
        assert "volatility_score" in result

    def test_evaluate_risk_score_matches_score_method(self):
        score_result = self.engine.score({"atr": 1500}, {"score": 0.5})
        eval_result = self.engine.evaluate({"atr": 1500}, {"score": 0.5})
        assert eval_result["risk_score"] == score_result

    def test_evaluate_penalties_includes_volatility(self):
        result = self.engine.evaluate({"atr": 0}, {"score": 1.0})
        assert "volatility" in result["penalties"]

    def test_evaluate_penalties_includes_atr(self):
        result = self.engine.evaluate({"atr": 3000}, {"score": 0})
        assert len(result["penalties"]) > 0

    def test_evaluate_no_penalties_when_no_risk(self):
        result = self.engine.evaluate({"atr": 0}, {"score": 0})
        assert result["penalties"] == {}
        assert result["risk_score"] == 1.0

    def test_evaluate_backward_compat_score_still_works(self):
        assert self.engine.score({"atr": 1000}, {"score": 0}) == 0.95
