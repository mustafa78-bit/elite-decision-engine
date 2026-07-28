from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionContext:
    """Context state of the platform harvested from independent subsystems."""

    indicators: dict[str, Any] = field(default_factory=dict)
    market_regime: dict[str, Any] = field(default_factory=dict)
    portfolio_status: dict[str, Any] = field(default_factory=dict)
    trust_scores: dict[str, Any] = field(default_factory=dict)
    learning_lessons: list[str] = field(default_factory=list)
    calibration_metrics: dict[str, Any] = field(default_factory=dict)
    discovery_narratives: list[str] = field(default_factory=list)
    risk_assessment: dict[str, Any] = field(default_factory=dict)
    advisor_votes: dict[str, Any] = field(default_factory=dict)
    graph_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
