"""DecisionTimeline — tracks decision events chronologically."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from decision.models import DecisionEvent, DecisionResult

logger = logging.getLogger(__name__)


class DecisionTimeline:
    """Record and retrieve decision events."""

    def __init__(self) -> None:
        self._events: dict[str, list[DecisionEvent]] = {}

    def record(
        self,
        symbol: str,
        event_type: str,
        description: str,
        source: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> DecisionEvent:
        event = DecisionEvent(
            event_type=event_type,
            description=description,
            source=source,
            details=details or {},
        )
        if symbol not in self._events:
            self._events[symbol] = []
        self._events[symbol].append(event)
        return event

    def get_events(self, symbol: str, limit: int = 50) -> list[DecisionEvent]:
        events = self._events.get(symbol, [])
        return events[-limit:]

    def get_all_events(self, limit: int = 100) -> list[DecisionEvent]:
        all_events: list[DecisionEvent] = []
        for symbol_events in self._events.values():
            all_events.extend(symbol_events)
        all_events.sort(key=lambda e: e.timestamp, reverse=True)
        return all_events[:limit]

    def build_timeline(self, result: DecisionResult) -> DecisionResult:
        symbol_events = self._events.get(result.symbol, [])
        result.timeline = symbol_events[-20:]
        return result

    def clear(self, symbol: Optional[str] = None) -> None:
        if symbol:
            self._events.pop(symbol, None)
        else:
            self._events.clear()
