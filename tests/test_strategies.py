"""Tests for strategy engine V2."""

import pandas as pd

from strategies.base import StrategyResult
from strategies.builtin import MeanReversionStrategy, TrendFollowStrategy
from strategies.registry import StrategyRegistry
from strategies.scoring import StrategyScore, StrategyScorer


class TestStrategyBase:
    def test_strategy_result_defaults(self):
        r = StrategyResult(signal="LONG")
        assert r.confidence == 0.0
        assert r.score == 0.0
        assert r.metadata == {}

    def test_strategy_result_confidence(self):
        r = StrategyResult(signal="SHORT", confidence=85.0)
        assert r.signal == "SHORT"
        assert r.confidence == 85.0


class TestStrategyRegistry:
    def test_register_and_list(self):
        registry = StrategyRegistry()
        registry.register(TrendFollowStrategy)
        registry.register(MeanReversionStrategy)
        names = registry.list()
        assert "trend_follow" in names
        assert "mean_reversion" in names

    def test_get_and_instantiate(self):
        registry = StrategyRegistry()
        registry.register(TrendFollowStrategy)
        cls = registry.get("trend_follow")
        assert cls is TrendFollowStrategy
        instance = registry.instantiate("trend_follow")
        assert isinstance(instance, TrendFollowStrategy)

    def test_get_nonexistent(self):
        registry = StrategyRegistry()
        assert registry.get("nonexistent") is None

    def test_count(self):
        registry = StrategyRegistry()
        assert registry.count() == 0
        registry.register(TrendFollowStrategy)
        assert registry.count() == 1


class TestTrendFollow:
    def test_evaluate_neutral_on_empty(self):
        s = TrendFollowStrategy()
        result = s.evaluate("BTC", None)
        assert result is None

    def test_evaluate_with_data(self):
        s = TrendFollowStrategy()
        import numpy as np
        dates = pd.date_range("2024-01-01", periods=100, freq="h")
        df = pd.DataFrame({"close": np.linspace(100, 120, 100)}, index=dates)
        result = s.evaluate("BTC", df)
        assert result is not None
        assert result.signal in ("LONG", "SHORT", "NEUTRAL")


class TestMeanReversion:
    def test_evaluate_neutral_on_empty(self):
        s = MeanReversionStrategy()
        result = s.evaluate("BTC", None)
        assert result is None

    def test_evaluate_with_data(self):
        s = MeanReversionStrategy()
        import numpy as np
        dates = pd.date_range("2024-01-01", periods=100, freq="h")
        df = pd.DataFrame({"close": np.linspace(100, 120, 100)}, index=dates)
        result = s.evaluate("BTC", df)
        assert result is not None
        assert isinstance(result.signal, str)


class TestStrategyScorer:
    def test_score_zero_trades(self):
        scorer = StrategyScorer()
        assert scorer.score(0, 0, 0, 0, 0, 0) == 0.0

    def test_score_perfect(self):
        scorer = StrategyScorer()
        score = scorer.score(win_rate=100, total_pnl=100000, avg_confidence=100, sharpe=3.0, max_drawdown=0, total_trades=100)
        assert score > 0.5

    def test_score_poor(self):
        scorer = StrategyScorer()
        score = scorer.score(win_rate=10, total_pnl=-5000, avg_confidence=20, sharpe=-1.0, max_drawdown=10000, total_trades=50)
        assert score < 0.3

    def test_compare(self):
        scorer = StrategyScorer()
        scores = [
            StrategyScore(name="A", win_rate=60, total_pnl=5000, avg_confidence=70, sharpe=1.5, max_drawdown=1000, total_trades=50),
            StrategyScore(name="B", win_rate=40, total_pnl=1000, avg_confidence=50, sharpe=0.5, max_drawdown=3000, total_trades=30),
        ]
        ranked = scorer.compare(scores)
        assert ranked[0].name == "A"
        assert ranked[0].overall_score >= ranked[1].overall_score
