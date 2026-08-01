from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from council.base import (
    DIRECTION_BEARISH,
    DIRECTION_BULLISH,
    DIRECTION_NEUTRAL,
    DIRECTION_PASS,
    AgentReport,
    BaseAgent,
)
from council.consensus import ConsensusEngine, CouncilReport, DEFAULT_WEIGHTS


class _BullishAgent(BaseAgent):
    def __init__(self, name: str = "Bullish", weight: float = 1.0):
        super().__init__(name=name, weight=weight)

    def evaluate(self, signal=None, scores=None, market_data=None, **kwargs):
        return AgentReport(
            agent_name=self.name,
            symbol=kwargs.get("symbol", "?"),
            direction=DIRECTION_BULLISH,
            confidence=0.9,
            score=0.8,
            reasoning=["Bullish signal"],
        )


class _BearishAgent(BaseAgent):
    def __init__(self, name: str = "Bearish", weight: float = 1.0):
        super().__init__(name=name, weight=weight)

    def evaluate(self, signal=None, scores=None, market_data=None, **kwargs):
        return AgentReport(
            agent_name=self.name,
            symbol=kwargs.get("symbol", "?"),
            direction=DIRECTION_BEARISH,
            confidence=0.8,
            score=0.7,
            reasoning=["Bearish signal"],
        )


class _NeutralAgent(BaseAgent):
    def __init__(self, name: str = "Neutral", weight: float = 1.0):
        super().__init__(name=name, weight=weight)

    def evaluate(self, signal=None, scores=None, market_data=None, **kwargs):
        return AgentReport(
            agent_name=self.name,
            symbol=kwargs.get("symbol", "?"),
            direction=DIRECTION_NEUTRAL,
            confidence=0.5,
            score=0.5,
            reasoning=["Neutral signal"],
        )


class TestConsensusEngine:
    def test_default_weights(self):
        assert DEFAULT_WEIGHTS["Technical"] == 0.25
        assert DEFAULT_WEIGHTS["Macro"] == 0.20
        assert sum(DEFAULT_WEIGHTS.values()) == 1.0

    def test_register_defaults(self):
        ce = ConsensusEngine()
        ce.register_defaults()
        assert len(ce.agents) == 6
        assert "Technical" in ce.agents
        assert "Trend" in ce.agents
        assert "Risk" in ce.agents
        assert "News" in ce.agents
        assert "Whale" in ce.agents
        assert "Macro" in ce.agents

    def test_register_agent(self):
        ce = ConsensusEngine()
        agent = _BullishAgent()
        ce.register_agent(agent)
        assert ce.get_agent("Bullish") is agent
        assert ce.agents["Bullish"] is agent

    def test_consensus_all_bullish(self):
        ce = ConsensusEngine(weights={"A": 1.0, "B": 1.0, "C": 1.0})
        ce.register_agent(_BullishAgent("A"))
        ce.register_agent(_BullishAgent("B"))
        ce.register_agent(_BullishAgent("C"))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.consensus_direction == DIRECTION_BULLISH
        assert report.consensus_score >= 0.7
        assert report.agreement_level == "strong"
        assert report.agent_count == 3
        assert report.sources_agreeing >= 2

    def test_consensus_all_bearish(self):
        ce = ConsensusEngine(weights={"A": 1.0, "B": 1.0})
        ce.register_agent(_BearishAgent("A"))
        ce.register_agent(_BearishAgent("B"))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.consensus_direction == DIRECTION_BEARISH
        assert report.consensus_score < 0.4

    def test_consensus_split(self):
        ce = ConsensusEngine(weights={"A": 1.0, "B": 1.0, "C": 1.0})
        ce.register_agent(_BullishAgent("A"))
        ce.register_agent(_NeutralAgent("B"))
        ce.register_agent(_BearishAgent("C"))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.consensus_direction in (DIRECTION_NEUTRAL, DIRECTION_BULLISH)
        assert 0.3 <= report.consensus_score <= 0.7

    def test_consensus_weighted_bullish(self):
        ce = ConsensusEngine(weights={"Bullish": 2.0, "Bearish": 0.5})
        ce.register_agent(_BullishAgent("Bullish"))
        ce.register_agent(_BearishAgent("Bearish"))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.consensus_direction == DIRECTION_BULLISH
        assert report.consensus_score >= 0.5

    def test_council_report_to_dict(self):
        report = CouncilReport(
            symbol="BTCUSDT",
            consensus_direction=DIRECTION_BULLISH,
            consensus_score=0.85,
            agreement_level="strong",
            agent_reports=[
                AgentReport(agent_name="A", symbol="BTCUSDT", direction=DIRECTION_BULLISH, confidence=0.9, score=0.8),
            ],
            agent_count=1,
            sources_agreeing=1,
            sources_disagreeing=0,
        )
        d = report.to_dict()
        assert d["symbol"] == "BTCUSDT"
        assert d["consensus_direction"] == DIRECTION_BULLISH
        assert len(d["agent_reports"]) == 1

    def test_stats(self):
        ce = ConsensusEngine()
        ce.register_agent(_BullishAgent("A"))
        ce.evaluate(signal=None, symbol="BTCUSDT")
        stats = ce.stats
        assert stats["agent_count"] == 1
        assert stats["evaluations"] == 1
        assert "A" in stats["agents"]
