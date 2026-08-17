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
from council.consensus import DEFAULT_WEIGHTS, ConsensusEngine, CouncilReport


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
        # Rebalanced 2026-08-17: Technical/Trend/Whale (treated as a leading
        # technical signal) carry most of the directional vote; News/Macro
        # lean toward a filter role instead of an equal seat at the table.
        assert DEFAULT_WEIGHTS["Technical"] == 0.30
        assert DEFAULT_WEIGHTS["Trend"] == 0.25
        assert DEFAULT_WEIGHTS["Whale"] == 0.15
        assert DEFAULT_WEIGHTS["Macro"] == 0.10
        assert DEFAULT_WEIGHTS["News"] == 0.05
        assert DEFAULT_WEIGHTS["Risk"] == 0.15
        assert sum(DEFAULT_WEIGHTS.values()) == 1.0

    def test_technical_and_trend_dominate_directional_vote(self):
        # The actual point of the rebalance: excluding Risk (non-directional,
        # doesn't compete for direction), Technical+Trend should now command
        # roughly 60%+ of the directional voting weight.
        directional_weight = sum(v for k, v in DEFAULT_WEIGHTS.items() if k != "Risk")
        technical_trend_share = (DEFAULT_WEIGHTS["Technical"] + DEFAULT_WEIGHTS["Trend"]) / directional_weight
        assert technical_trend_share >= 0.6

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

    def test_evaluate_default_does_not_call_ai(self):
        # include_ai_opinion defaults to False -- a plain evaluate() must
        # never make an AI call, so it stays exactly as fast/cheap as
        # before council/ai_advisor.py existed.
        ce = ConsensusEngine(weights={"Bullish": 1.0})
        ce.register_agent(_BullishAgent())
        with patch("council.ai_advisor.get_ai_opinion") as mock_opinion:
            report = ce.evaluate(symbol="BTC")
        mock_opinion.assert_not_called()
        assert report.ai_opinion is None

    def test_evaluate_with_ai_opinion_true_calls_advisor(self):
        ce = ConsensusEngine(weights={"Bullish": 1.0})
        ce.register_agent(_BullishAgent())
        with patch("council.ai_advisor.get_ai_opinion", return_value="Looks fine.") as mock_opinion:
            report = ce.evaluate(symbol="BTC", include_ai_opinion=True)
        mock_opinion.assert_called_once_with(report)
        assert report.ai_opinion == "Looks fine."

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


class _RiskVetoAgent(BaseAgent):
    def __init__(self, name: str = "Risk", direction: str = DIRECTION_PASS):
        super().__init__(name=name, is_directional=False)
        self._direction = direction

    def evaluate(self, signal=None, scores=None, market_data=None, **kwargs):
        return AgentReport(
            agent_name=self.name,
            symbol=kwargs.get("symbol", "?"),
            direction=self._direction,
            confidence=0.9,
            score=0.2,
            reasoning=["High risk situation"],
        )


class TestConsensusVetoAndAgreement:
    def test_consensus_risk_veto(self):
        ce = ConsensusEngine(weights={"Bullish": 1.0, "Risk": 1.0})
        ce.register_agent(_BullishAgent("Bullish"))
        ce.register_agent(_RiskVetoAgent("Risk", DIRECTION_PASS))

        # Risk PASS veto must override Bullish and force final consensus_direction to DIRECTION_PASS
        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.consensus_direction == DIRECTION_PASS
        assert report.consensus_score == 0.0
        assert report.risk_veto is True
        assert report.risk_veto_reason == "High risk situation"

    def test_consensus_risk_no_veto_if_not_pass(self):
        ce = ConsensusEngine(weights={"Bullish": 1.0, "Risk": 1.0})
        ce.register_agent(_BullishAgent("Bullish"))
        ce.register_agent(_RiskVetoAgent("Risk", DIRECTION_NEUTRAL))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.consensus_direction == DIRECTION_BULLISH
        assert report.risk_veto is False

    def test_consensus_risk_non_directional_exclusion(self):
        ce = ConsensusEngine(weights={"Bearish1": 1.0, "Bearish2": 1.0, "Risk": 1.0})
        ce.register_agent(_BearishAgent("Bearish1"))
        ce.register_agent(_BearishAgent("Bearish2"))
        ce.register_agent(_RiskVetoAgent("Risk", DIRECTION_BULLISH)) # Non-directional BULLISH (e.g. Risk is low)

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        # Risk (non-directional) must be excluded from directional sharing tally,
        # so Bearish wins despite Risk voting Bullish
        assert report.consensus_direction == DIRECTION_BEARISH

    def test_consensus_agreement_level_split(self):
        ce = ConsensusEngine(weights={"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0})
        ce.register_agent(_BullishAgent("A"))
        ce.register_agent(_BullishAgent("B"))
        ce.register_agent(_BearishAgent("C"))
        ce.register_agent(_BearishAgent("D"))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        # Split (2 bullish vs 2 bearish) must not be "strong"
        assert report.agreement_level in ("moderate", "weak")

    def test_sources_agreeing_excludes_non_directional_agent(self):
        # 2 Bullish (agree with consensus) + 1 Bearish (disagrees) -> consensus
        # is BULLISH among the 3 real directional agents. The non-directional
        # Risk agent's direction is a risk-level category, not a market vote --
        # even though it coincidentally reports BULLISH here, it must not be
        # counted as "agreeing".
        ce = ConsensusEngine(weights={"A": 1.0, "B": 1.0, "C": 1.0, "Risk": 1.0})
        ce.register_agent(_BullishAgent("A"))
        ce.register_agent(_BullishAgent("B"))
        ce.register_agent(_BearishAgent("C"))
        ce.register_agent(_RiskVetoAgent("Risk", DIRECTION_BULLISH))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.consensus_direction == DIRECTION_BULLISH
        assert report.agent_count == 4
        # Only the 3 directional agents count: 2 agreeing (A, B), 1 disagreeing (C).
        assert report.sources_agreeing == 2
        assert report.sources_disagreeing == 1

    def test_sources_agreeing_zero_on_risk_veto(self):
        # On a risk veto, the directional vote never ran -- reporting the
        # directional agents as "disagreeing" with DIRECTION_PASS would be
        # misleading, so both counts should be 0.
        ce = ConsensusEngine(weights={"Bullish": 1.0, "Risk": 1.0})
        ce.register_agent(_BullishAgent("Bullish"))
        ce.register_agent(_RiskVetoAgent("Risk", DIRECTION_PASS))

        report = ce.evaluate(signal=None, symbol="BTCUSDT")
        assert report.risk_veto is True
        assert report.sources_agreeing == 0
        assert report.sources_disagreeing == 0
