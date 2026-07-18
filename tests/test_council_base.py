from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from council.base import (
    DIRECTION_BEARISH,
    DIRECTION_BULLISH,
    DIRECTION_NEUTRAL,
    DIRECTION_PASS,
    AgentReport,
    BaseAgent,
)


class TestAgentReport:
    def test_defaults(self) -> None:
        r = AgentReport(agent_name="TestAgent", symbol="BTCUSDT")
        assert r.agent_name == "TestAgent"
        assert r.symbol == "BTCUSDT"
        assert r.direction == DIRECTION_NEUTRAL
        assert r.confidence == 0.0
        assert r.score == 0.0
        assert r.reasoning == []
        assert r.data_points == {}
        assert r.latency_ms == 0.0
        assert r.timestamp != ""

    def test_summary(self) -> None:
        r = AgentReport(
            agent_name="Tech",
            symbol="ETHUSDT",
            direction=DIRECTION_BULLISH,
            confidence=0.85,
            score=0.75,
        )
        summary = r.summary
        assert "Tech" in summary
        assert "ETHUSDT" in summary
        assert "BULLISH" in summary
        assert "0.85" in summary

    def test_to_dict(self) -> None:
        r = AgentReport(
            agent_name="Risk",
            symbol="BTCUSDT",
            direction=DIRECTION_BEARISH,
            confidence=0.3,
            score=0.4,
            reasoning=["High volatility"],
            data_points={"atr": 1500},
        )
        d = r.to_dict()
        assert d["agent_name"] == "Risk"
        assert d["direction"] == DIRECTION_BEARISH
        assert d["reasoning"] == ["High volatility"]
        assert d["data_points"]["atr"] == 1500


class TestBaseAgent:
    def test_abstract_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseAgent("Bad")  # type: ignore

    def test_concrete_agent(self) -> None:
        agent = _create_test_agent()
        assert agent.name == "Test"
        assert agent.weight == 1.0
        assert agent.priority == 5

    def test_timed_evaluate_success(self) -> None:
        agent = _create_test_agent()
        report = agent._timed_evaluate(symbol="BTCUSDT")
        assert report.agent_name == "Test"
        assert report.symbol == "BTCUSDT"
        assert report.direction == DIRECTION_BULLISH
        assert report.confidence == 0.8
        assert report.latency_ms >= 0
        assert agent.stats["eval_count"] == 1
        assert agent.stats["error_count"] == 0

    def test_timed_evaluate_error(self) -> None:
        agent = _create_test_agent(raise_error=True)
        report = agent._timed_evaluate(symbol="BTCUSDT")
        assert report.agent_name == "Test"
        assert report.direction == DIRECTION_PASS
        assert report.confidence == 0.0
        assert "Evaluation error" in report.reasoning[0]
        assert agent.stats["error_count"] == 1

    def test_stats(self) -> None:
        agent = _create_test_agent()
        agent._timed_evaluate(symbol="BTCUSDT")
        agent._timed_evaluate(symbol="ETHUSDT")
        stats = agent.stats
        assert stats["name"] == "Test"
        assert stats["eval_count"] == 2
        assert stats["avg_latency_ms"] >= 0


class _TestConcreteAgent(BaseAgent):
    def __init__(self, raise_error: bool = False) -> None:
        super().__init__("Test")
        self._raise_error = raise_error

    def evaluate(self, signal=None, scores=None, market_data=None, **kwargs):
        if self._raise_error:
            raise RuntimeError("Something went wrong")
        return AgentReport(
            agent_name=self.name,
            symbol=kwargs.get("symbol", "?"),
            direction=DIRECTION_BULLISH,
            confidence=0.8,
            score=0.7,
            reasoning=["All good"],
        )


def _create_test_agent(raise_error: bool = False) -> _TestConcreteAgent:
    return _TestConcreteAgent(raise_error=raise_error)
