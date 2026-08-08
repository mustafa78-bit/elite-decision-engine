from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any, Optional

from council.base import (
    DIRECTION_BEARISH,
    DIRECTION_BULLISH,
    DIRECTION_NEUTRAL,
    DIRECTION_PASS,
    AgentReport,
    BaseAgent,
    normalize_direction,
)
from council.macro_agent import MacroAgent
from council.news_agent import NewsAgent
from council.risk_agent import RiskAgent
from council.technical_agent import TechnicalAgent
from council.trend_agent import TrendAgent
from council.whale_agent import WhaleAgent
from execution.pipeline import TradingSignal
from services.coordinator_service import CoordinatorService

logger = logging.getLogger(__name__)


@dataclass
class CouncilReport:
    symbol: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    consensus_direction: str = DIRECTION_NEUTRAL
    consensus_score: float = 0.0
    agreement_level: str = ""
    agent_reports: list[AgentReport] = field(default_factory=list)
    coordinator_report: dict[str, Any] | None = None
    agent_count: int = 0
    sources_agreeing: int = 0
    sources_disagreeing: int = 0
    risk_veto: bool = False
    risk_veto_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["agent_reports"] = [r.to_dict() for r in self.agent_reports]
        return d


DEFAULT_WEIGHTS: dict[str, float] = {
    "Technical": 0.25,
    "Trend": 0.20,
    "Risk": 0.15,
    "News": 0.10,
    "Whale": 0.10,
    "Macro": 0.20,
}

class ConsensusEngine:
    """Collects reports from all registered agents and produces a unified council report.

    Integrates with the existing CoordinatorService for conflict resolution
    and recommendation ranking.
    """

    def __init__(
        self,
        coordinator: CoordinatorService | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.coordinator = coordinator or CoordinatorService()
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self.agents: dict[str, BaseAgent] = {}
        self._eval_count = 0

    def register_agent(self, agent: BaseAgent) -> None:
        self.agents[agent.name] = agent
        self.coordinator.intelligence_registry.register(
            name=agent.name,
            source_type="agent",
            instance=agent,
            weight=self.weights.get(agent.name, 1.0),
            priority=agent.priority,
        )
        self.coordinator.ai_source_registry.register(
            name=agent.name,
            version="1.0",
            weight=self.weights.get(agent.name, 1.0),
            priority=agent.priority,
            capabilities=[agent.name.lower()],
        )
        logger.info(
            "Registered agent %s with weight=%.2f priority=%s",
            agent.name,
            self.weights.get(agent.name, 1.0),
            agent.priority,
        )

    def register_defaults(self) -> None:
        agents = [
            TechnicalAgent(),
            TrendAgent(),
            RiskAgent(),
            NewsAgent(),
            WhaleAgent(),
            MacroAgent(),
        ]
        for agent in agents:
            self.register_agent(agent)

    def evaluate(
        self,
        signal: TradingSignal | None = None,
        scores: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> CouncilReport:
        self._eval_count += 1
        symbol = getattr(signal, "symbol", "?") if signal else kwargs.get("symbol", "?")
        side = getattr(signal, "side", "LONG") if signal else kwargs.get("side", "LONG")

        reports: list[AgentReport] = []
        for name, agent in self.agents.items():
            report = agent._timed_evaluate(signal=signal, scores=scores, **kwargs)
            reports.append(report)

        consensus_direction, consensus_score, agreement, risk_veto, risk_veto_reason = self._compute_consensus(reports, side)

        coordinator_report: dict[str, Any] | None = None
        try:
            coordinator_report = self.coordinator.evaluate(signal, scores, reports).to_dict()
        except Exception as e:
            logger.warning("Coordinator evaluation failed: %s", e)

        if risk_veto:
            # The directional vote never ran (short-circuited by the veto), so
            # there's no real agreement/disagreement to report against a
            # DIRECTION_PASS "consensus" -- reporting directional agents as
            # "disagreeing" with a veto they never weighed in on would be
            # misleading.
            agreeing = 0
            disagreeing = 0
        else:
            # Only tally agreement among directional agents -- a non-directional
            # agent (e.g. RiskAgent, whose "direction" means a risk-level
            # category, not a market-direction vote) has no meaningful
            # agree/disagree relationship to consensus_direction, matching the
            # same population _compute_consensus() already restricts its
            # direction vote to.
            directional_reports = [
                r for r in reports
                if getattr(self.agents.get(r.agent_name), "is_directional", True)
            ]
            agreeing = sum(
                1 for r in directional_reports
                if r.direction == consensus_direction and r.confidence > 0.3
            )
            disagreeing = len(directional_reports) - agreeing

        return CouncilReport(
            symbol=symbol,
            consensus_direction=consensus_direction,
            consensus_score=round(consensus_score, 4),
            agreement_level=agreement,
            agent_reports=reports,
            coordinator_report=coordinator_report,
            agent_count=len(reports),
            sources_agreeing=agreeing,
            sources_disagreeing=disagreeing,
            risk_veto=risk_veto,
            risk_veto_reason=risk_veto_reason,
        )

    def _compute_consensus(
        self, reports: list[AgentReport], side: str
    ) -> tuple[str, float, str, bool, str | None]:
        if not reports:
            return DIRECTION_NEUTRAL, 0.0, "none", False, None

        # Split reports into directional and non-directional groups
        directional_reports: list[AgentReport] = []
        non_directional_reports: list[AgentReport] = []

        for r in reports:
            agent = self.agents.get(r.agent_name)
            is_dir = getattr(agent, "is_directional", True) if agent is not None else True
            if is_dir:
                directional_reports.append(r)
            else:
                non_directional_reports.append(r)

        # Non-directional Veto check
        risk_veto = False
        risk_veto_reason = None
        for r in non_directional_reports:
            if r.direction == DIRECTION_PASS:
                risk_veto = True
                risk_veto_reason = " ".join(r.reasoning)
                break

        if risk_veto:
            return DIRECTION_PASS, 0.0, "none", True, risk_veto_reason

        direction_weights: dict[str, float] = {}
        total_weight = 0.0

        for report in directional_reports:
            weight = self.weights.get(report.agent_name, 1.0)
            combined = report.confidence * weight
            direction_weights[report.direction] = direction_weights.get(report.direction, 0.0) + combined
            total_weight += weight

        if total_weight == 0 or not directional_reports:
            return DIRECTION_NEUTRAL, 0.0, "none", False, None

        bullish_total = direction_weights.get(DIRECTION_BULLISH, 0.0)
        bearish_total = direction_weights.get(DIRECTION_BEARISH, 0.0)
        neutral_total = direction_weights.get(DIRECTION_NEUTRAL, 0.0)

        bullish_share = bullish_total / total_weight
        bearish_share = bearish_total / total_weight
        neutral_share = neutral_total / total_weight

        if bullish_share > bearish_share and bullish_share > neutral_share:
            direction = DIRECTION_BULLISH
            score_normalized = 0.5 + bullish_share / 2.0
        elif bearish_share > bullish_share and bearish_share > neutral_share:
            direction = DIRECTION_BEARISH
            score_normalized = 0.5 - bearish_share / 2.0
        else:
            direction = DIRECTION_NEUTRAL
            score_normalized = 0.5

        score_normalized = max(0.0, min(1.0, score_normalized))

        # Fraction of directional reports that match the winning consensus_direction with confidence > 0.5
        confident_directional = [r for r in directional_reports if r.confidence > 0.5]
        if not confident_directional:
            agreement = "none"
        else:
            matching_confident = sum(
                1 for r in directional_reports
                if r.direction == direction and r.confidence > 0.5
            )
            fraction = matching_confident / len(directional_reports)
            if fraction >= 0.8:
                agreement = "strong"
            elif fraction >= 0.5:
                agreement = "moderate"
            else:
                agreement = "weak"

        return direction, round(score_normalized, 4), agreement, False, None

    def get_agent(self, name: str) -> BaseAgent | None:
        return self.agents.get(name)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "agent_count": len(self.agents),
            "evaluations": self._eval_count,
            "agents": {name: agent.stats for name, agent in self.agents.items()},
        }
