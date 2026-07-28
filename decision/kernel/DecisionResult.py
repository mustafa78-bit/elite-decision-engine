from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from decision.kernel.DecisionEvidence import DecisionEvidence
from decision.kernel.DecisionReasoning import DecisionReasoning
from decision.kernel.DecisionTimeline import TimelineEvent


@dataclass
class DecisionResult:
    """The stable platform-wide single source of truth for decisions."""

    # 1. Core Identification
    symbol: str
    side: str
    decision: str  # Action recommendation: STRONG_APPROVE, APPROVE, WATCH, REJECT
    decision_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )  # SHA-256 or UUID
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # 2. Score Metrics
    score: float = 0.0
    confidence: float = 0.0
    probability: float = 0.0
    risk_score: float = 0.0
    priority: float = 0.0

    # 3. Contextual Subsystems
    trust: dict[str, Any] = field(default_factory=dict)
    risk: dict[str, Any] = field(default_factory=dict)
    portfolio_impact: dict[str, Any] = field(default_factory=dict)
    market_regime: dict[str, Any] = field(default_factory=dict)
    learning_context: dict[str, Any] = field(default_factory=dict)
    calibration_status: dict[str, Any] = field(default_factory=dict)
    graph_context: dict[str, Any] = field(default_factory=dict)
    advisor_votes: dict[str, Any] = field(default_factory=dict)

    # 4. Explanations
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    founder_summary: str = ""

    # 5. Full Cognitive Traces
    evidence: list[DecisionEvidence] = field(default_factory=list)
    reasoning: list[DecisionReasoning] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # --- Backward Compatibility Properties ---

    @property
    def reasons_list(self) -> list[str]:
        return self.reasons

    @property
    def warnings_list(self) -> list[str]:
        return self.warnings

    @property
    def signals_list(self) -> list[str]:
        return self.signals

    @property
    def intelligence_summary(self) -> dict[str, Any]:
        """Backward compatibility helper for UI dashboards."""
        return {
            "fear_greed": self.market_regime.get("fear_greed", "UNKNOWN"),
            "funding_level": self.market_regime.get("funding_level", "UNKNOWN"),
            "liquidity_level": self.market_regime.get("liquidity_level", "UNKNOWN"),
            "market_session": self.market_regime.get("market_session", "UNKNOWN"),
            "intelligence_confidence": self.confidence,
            "features_available": len(self.market_regime),
            "trust_score": self.trust.get("score", 0.0),
            "priority": self.priority,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "founder_summary": self.founder_summary,
        }

    @property
    def feature_summary(self) -> dict[str, Any]:
        """Backward compatibility helper."""
        return self.market_regime

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for APIs and dashboards."""
        return {
            "decision_id": self.decision_id,
            "symbol": self.symbol,
            "side": self.side,
            "decision": self.decision,
            "timestamp": self.timestamp,
            "score": self.score,
            "confidence": self.confidence,
            "probability": self.probability,
            "risk_score": self.risk_score,
            "priority": self.priority,
            "trust": self.trust,
            "risk": self.risk,
            "portfolio_impact": self.portfolio_impact,
            "market_regime": self.market_regime,
            "learning_context": self.learning_context,
            "calibration_status": self.calibration_status,
            "graph_context": self.graph_context,
            "advisor_votes": self.advisor_votes,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "signals": self.signals,
            "founder_summary": self.founder_summary,
            "metadata": self.metadata,
        }
