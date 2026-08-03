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


from typing import Callable, Any
from database import get_session, CommanderMemoryEntry

class CommanderMemory:

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self.session_factory = session_factory
        self._briefings_cache: list[BriefingRecord] = []
        self._recommendations_cache: list[RecommendationRecord] = []
        self._preferences_cache: dict[str, str] = {}

    def record_briefing(self, kind: str, text: str) -> None:
        record = BriefingRecord(kind=kind, text=text)
        self._briefings_cache.append(record)

        session = self.session_factory()
        try:
            entry = CommanderMemoryEntry(
                entry_type="BRIEFING",
                key=kind,
                value=text,
                timestamp=record.timestamp,
            )
            session.add(entry)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Failed to record briefing memory: %s", e)
        finally:
            session.close()

    def recent_briefings(self, limit: int = 5) -> list[BriefingRecord]:
        session = self.session_factory()
        try:
            entries = (
                session.query(CommanderMemoryEntry)
                .filter(CommanderMemoryEntry.entry_type == "BRIEFING")
                .order_by(CommanderMemoryEntry.id.desc())
                .limit(limit)
                .all()
            )
            records = []
            for entry in reversed(entries):
                records.append(
                    BriefingRecord(
                        kind=entry.key or "",
                        text=entry.value or "",
                        timestamp=entry.timestamp or datetime.now(timezone.utc).isoformat(),
                    )
                )
            self._briefings_cache = records
            return records
        except Exception as e:
            logger.error("Failed to retrieve recent briefings: %s", e)
            return self._briefings_cache[-limit:]
        finally:
            session.close()

    def last_briefing(self, kind: Optional[str] = None) -> Optional[BriefingRecord]:
        session = self.session_factory()
        try:
            query = session.query(CommanderMemoryEntry).filter(CommanderMemoryEntry.entry_type == "BRIEFING")
            if kind is not None:
                query = query.filter(CommanderMemoryEntry.key == kind)
            entry = query.order_by(CommanderMemoryEntry.id.desc()).first()
            if entry is None:
                return None
            return BriefingRecord(
                kind=entry.key or "",
                text=entry.value or "",
                timestamp=entry.timestamp or datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            logger.error("Failed to retrieve last briefing: %s", e)
            if kind is None:
                return self._briefings_cache[-1] if self._briefings_cache else None
            for b in reversed(self._briefings_cache):
                if b.kind == kind:
                    return b
            return None
        finally:
            session.close()

    def record_recommendation(self, query: str, room: str, response_text: str) -> None:
        record = RecommendationRecord(query=query, room=room, response_text=response_text)
        self._recommendations_cache.append(record)

        session = self.session_factory()
        try:
            entry = CommanderMemoryEntry(
                entry_type="RECOMMENDATION",
                query=query,
                room=room,
                value=response_text,
                timestamp=record.timestamp,
            )
            session.add(entry)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Failed to record recommendation memory: %s", e)
        finally:
            session.close()

    def recent_recommendations(self, limit: int = 5, room: Optional[str] = None) -> list[RecommendationRecord]:
        session = self.session_factory()
        try:
            query = (
                session.query(CommanderMemoryEntry)
                .filter(CommanderMemoryEntry.entry_type == "RECOMMENDATION")
            )
            if room is not None:
                query = query.filter(CommanderMemoryEntry.room == room)
            entries = (
                query.order_by(CommanderMemoryEntry.id.desc())
                .limit(limit)
                .all()
            )
            records = []
            for entry in reversed(entries):
                records.append(
                    RecommendationRecord(
                        query=entry.query or "",
                        room=entry.room or "",
                        response_text=entry.value or "",
                        timestamp=entry.timestamp or datetime.now(timezone.utc).isoformat(),
                    )
                )
            self._recommendations_cache = records
            return records
        except Exception as e:
            logger.error("Failed to retrieve recent recommendations: %s", e)
            filtered_cache = self._recommendations_cache
            if room is not None:
                filtered_cache = [r for r in filtered_cache if r.room == room]
            return filtered_cache[-limit:]
        finally:
            session.close()

    def set_preference(self, key: str, value: str) -> None:
        self._preferences_cache[key] = value

        session = self.session_factory()
        try:
            entry = (
                session.query(CommanderMemoryEntry)
                .filter(
                    CommanderMemoryEntry.entry_type == "PREFERENCE",
                    CommanderMemoryEntry.key == key
                )
                .first()
            )
            if entry is not None:
                entry.value = value
            else:
                entry = CommanderMemoryEntry(
                    entry_type="PREFERENCE",
                    key=key,
                    value=value,
                )
                session.add(entry)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Failed to set user preference memory: %s", e)
        finally:
            session.close()

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        session = self.session_factory()
        try:
            entry = (
                session.query(CommanderMemoryEntry)
                .filter(
                    CommanderMemoryEntry.entry_type == "PREFERENCE",
                    CommanderMemoryEntry.key == key
                )
                .first()
            )
            if entry is None:
                return default
            self._preferences_cache[key] = entry.value or ""
            return entry.value
        except Exception as e:
            logger.error("Failed to get user preference: %s", e)
            return self._preferences_cache.get(key, default)
        finally:
            session.close()

    def status(self) -> dict:
        session = self.session_factory()
        try:
            briefings_count = (
                session.query(CommanderMemoryEntry)
                .filter(CommanderMemoryEntry.entry_type == "BRIEFING")
                .count()
            )
            recommendations_count = (
                session.query(CommanderMemoryEntry)
                .filter(CommanderMemoryEntry.entry_type == "RECOMMENDATION")
                .count()
            )
            preferences_count = (
                session.query(CommanderMemoryEntry)
                .filter(CommanderMemoryEntry.entry_type == "PREFERENCE")
                .count()
            )
            latest_briefing = (
                session.query(CommanderMemoryEntry)
                .filter(CommanderMemoryEntry.entry_type == "BRIEFING")
                .order_by(CommanderMemoryEntry.id.desc())
                .first()
            )
            return {
                "briefings_stored": briefings_count,
                "recommendations_stored": recommendations_count,
                "preferences_count": preferences_count,
                "recent_briefing_kind": latest_briefing.key if latest_briefing else None,
            }
        except Exception as e:
            logger.error("Failed to get memory status: %s", e)
            return {
                "briefings_stored": len(self._briefings_cache),
                "recommendations_stored": len(self._recommendations_cache),
                "preferences_count": len(self._preferences_cache),
                "recent_briefing_kind": self._briefings_cache[-1].kind if self._briefings_cache else None,
            }
        finally:
            session.close()
