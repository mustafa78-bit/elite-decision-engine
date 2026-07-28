from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DecisionReasoning:
    """Structure describing a single step in the decision reasoning process."""

    step: str  # e.g., "Observe", "Trust", "Learn", "Calibrate"
    description: str
    impact: float = 0.0  # Weight or score adjustment (+/-)
    status: str = "SUCCESS"  # SUCCESS, WARNING, FAILURE
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
