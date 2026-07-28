from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DecisionEvidence:
    """An empirical piece of evidence supporting or warning about a decision."""

    source: str  # e.g., "WhaleIntelligence", "AICouncil", "Indicators"
    metric_name: str
    metric_value: Any
    confidence: float = 1.0
    trust_score: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
