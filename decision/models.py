from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DecisionEvent:
    event_type: str
    description: str
    source: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DecisionResult:
    symbol: str
    side: str
    decision: str

    score: float = 0.0
    confidence: float = 0.0
    probability: float = 0.0
    risk_score: float = 0.0

    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)

    timeline: list[DecisionEvent] = field(default_factory=list)
    intelligence_summary: dict[str, Any] = field(default_factory=dict)
    feature_summary: dict[str, Any] = field(default_factory=dict)

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
