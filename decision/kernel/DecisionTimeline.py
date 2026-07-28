from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class TimelineEvent:
    """A trace representing a point in the cognitive decision flow."""

    stage: str  # e.g., "Observe", "Connect", "Learn", "Decide"
    description: str
    source: str = "DecisionKernel"
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DecisionTimeline:
    """Chronological tracker of a request's journey through the cognitive loop."""

    def __init__(self) -> None:
        self.events: list[TimelineEvent] = []

    def record(self, stage: str, description: str, source: str = "DecisionKernel", details: Optional[dict[str, Any]] = None) -> None:
        """Add a stage event to the timeline."""
        self.events.append(
            TimelineEvent(
                stage=stage,
                description=description,
                source=source,
                details=details or {},
            )
        )

    def to_list(self) -> list[dict[str, Any]]:
        """Convert all timeline events to dictionaries."""
        return [
            {
                "stage": e.stage,
                "description": e.description,
                "source": e.source,
                "details": e.details,
                "timestamp": e.timestamp,
            }
            for e in self.events
        ]
