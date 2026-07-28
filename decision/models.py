from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Import the single authoritative platform-wide decision contract
from decision.kernel.DecisionResult import DecisionResult


@dataclass
class DecisionEvent:
    """Legacy DecisionEvent class kept for backward compatibility."""

    event_type: str
    description: str
    source: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


__all__ = [
    "DecisionResult",
    "DecisionEvent",
]
