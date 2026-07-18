from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class BriefingRecord:
    kind: str
    text: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class RecommendationRecord:
    query: str
    room: str
    response_text: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class UserPreference:
    key: str
    value: str


class CommanderMemory:

    def __init__(self) -> None:
        self._briefings: list[BriefingRecord] = []
        self._recommendations: list[RecommendationRecord] = []
        self._preferences: dict[str, str] = {}

    def record_briefing(self, kind: str, text: str) -> None:
        self._briefings.append(BriefingRecord(kind=kind, text=text))

    def recent_briefings(self, limit: int = 5) -> list[BriefingRecord]:
        return self._briefings[-limit:]

    def last_briefing(self, kind: Optional[str] = None) -> Optional[BriefingRecord]:
        if kind is None:
            return self._briefings[-1] if self._briefings else None
        for b in reversed(self._briefings):
            if b.kind == kind:
                return b
        return None

    def record_recommendation(self, query: str, room: str, response_text: str) -> None:
        self._recommendations.append(
            RecommendationRecord(query=query, room=room, response_text=response_text)
        )

    def recent_recommendations(self, limit: int = 5) -> list[RecommendationRecord]:
        return self._recommendations[-limit:]

    def set_preference(self, key: str, value: str) -> None:
        self._preferences[key] = value

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._preferences.get(key, default)

    def status(self) -> dict:
        return {
            "briefings_stored": len(self._briefings),
            "recommendations_stored": len(self._recommendations),
            "preferences_count": len(self._preferences),
            "recent_briefing_kind": self._briefings[-1].kind if self._briefings else None,
        }
