from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

from council.base import (
    DIRECTION_BEARISH,
    DIRECTION_BULLISH,
    DIRECTION_NEUTRAL,
    DIRECTION_PASS,
    AgentReport,
    BaseAgent,
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
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    consensus_direction: str = DIRECTION_NEUTRAL
    consensus_score: float = 0.0
    agreement_level: str = ""
    agent_reports: list[AgentReport] = field(default_factory=list)
    coordinator_report: Optional[dict[str, Any]] = None
    agent_count: int = 0
    sources_agreeing: int = 0
    sources_disagreeing: int = 0

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

DIRECTION_SCORES: dict[str, float] = {
    DIRECTION_BULLISH: 1.0,
    DIRECTION_NEUTRAL: 0.5,
    DIRECTION_BEARISH: 0.0,
    DIRECTION_PASS: 0.0,
}

SCORE_TO_DIRECTION: list[tuple[float, str]] = [
    (0.7, DIRECTION_BULLISH),
    (0.4, DIRECTION_NEUTRAL),
    (0.0, DIRECTION_BEARISH),
]


class ConsensusEngine:
    """Collects reports from all registered agents and produces a unified council report.

    Integrates with the existing CoordinatorService for conflict resolution
    and recommendation ranking.
    """

    def __init__(
        self,
        coordinator: Optional[CoordinatorService] = None,
        weights: Optional[dict[str, float]] = None,
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
        signal: Optional[TradingSignal] = None,
        scores: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> CouncilReport:
        self._eval_count += 1
        symbol = getattr(signal, "symbol", "?") if signal else kwargs.get("symbol", "?")

        reports: list[AgentReport] = []
        for name, agent in self.agents.items():
            report = agent._timed_evaluate(signal=signal, scores=scores, **kwargs)
            reports.append(report)

        consensus_direction, consensus_score, agreement = self._compute_consensus(reports)

        coordinator_report: Optional[dict[str, Any]] = None
        try:
            coordinator_report = self.coordinator.evaluate(signal, scores).to_dict()
        except Exception as e:
            logger.warning("Coordinator evaluation failed: %s", e)

        agreeing = sum(
            1 for r in reports
            if r.direction == consensus_direction and r.confidence > 0.3
        )
        disagreeing = len(reports) - agreeing

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
        )

    def _compute_consensus(
        self, reports: list[AgentReport]
    ) -> tuple[str, float, str]:
        if not reports:
            return DIRECTION_NEUTRAL, 0.0, "none"

        direction_weights: dict[str, float] = {}
        total_weight = 0.0

        for report in reports:
            weight = self.weights.get(report.agent_name, 1.0)
            combined = report.confidence * weight
            direction_weights[report.direction] = direction_weights.get(report.direction, 0.0) + combined
            total_weight += weight

        if total_weight == 0:
            return DIRECTION_NEUTRAL, 0.0, "none"

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

        high_conf = sum(1 for r in reports if r.confidence > 0.5)
        low_conf = len(reports) - high_conf

        if low_conf == 0:
            agreement = "strong"
        elif low_conf <= len(reports) // 2:
            agreement = "moderate"
        else:
            agreement = "weak"

        if high_conf == 0:
            agreement = "none"

        return direction, round(score_normalized, 4), agreement

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self.agents.get(name)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "agent_count": len(self.agents),
            "evaluations": self._eval_count,
            "agents": {name: agent.stats for name, agent in self.agents.items()},
        }
