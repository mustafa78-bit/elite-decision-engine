from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List
from core.orchestrator.models import IntelligenceEvent

logger = logging.getLogger(__name__)


class EventBus:
    """A lightweight observable message hub tracking chronological intelligence events."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[IntelligenceEvent], None]]] = {}
        self._history: List[IntelligenceEvent] = []

    def subscribe(self, event_type: str, callback: Callable[[IntelligenceEvent], None]) -> None:
        """Register a subscriber callback for a specific event type, or '*' for all events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: IntelligenceEvent) -> None:
        """Publish an event to all matched subscribers and store it in chronological history."""
        self._history.append(event)
        logger.info("[EventBus] Published Event: %s on symbol %s", event.event_type, event.symbol)

        # Specific subscribers
        if event.event_type in self._subscribers:
            for cb in self._subscribers[event.event_type]:
                try:
                    cb(event)
                except Exception as e:
                    logger.error("[EventBus] Subscriber failed on %s: %s", event.event_type, e)

        # Wildcard subscribers
        if "*" in self._subscribers:
            for cb in self._subscribers["*"]:
                try:
                    cb(event)
                except Exception as e:
                    logger.error("[EventBus] Wildcard subscriber failed: %s", e)

    def get_history(self, limit: int = 100) -> List[IntelligenceEvent]:
        """Retrieve historical timeline events chronologically."""
        return self._history[-limit:]

    def clear(self) -> None:
        """Reset historical logs and subscribers."""
        self._history.clear()
        self._subscribers.clear()


# Global Singleton instance for internal module orchestration
event_bus = EventBus()
