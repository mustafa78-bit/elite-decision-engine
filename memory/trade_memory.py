from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from typing import Callable, Any

from database import JournalEntry, get_session

logger = logging.getLogger(__name__)


@dataclass
class TradeMemoryEntry:
    id: int = 0
    symbol: str = ""
    side: str = ""
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    pnl: float = 0.0
    result: str = "PENDING"
    entry_reason: str = ""
    exit_reason: Optional[str] = None
    conditions: dict[str, Any] = field(default_factory=dict)
    lessons: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: Optional[str] = None


class TradeMemory:
    """Persistent trade memory system storing setup, conditions, results, and lessons."""

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self._cache: dict[int, TradeMemoryEntry] = {}
        self.session_factory = session_factory

    def record(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        entry_reason: str,
        conditions: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ) -> int:
        """Record a new trade in memory (and journal)."""
        session = self.session_factory()
        try:
            entry = JournalEntry(
                symbol=symbol.upper(),
                side=side.upper(),
                entry_price=entry_price,
                entry_reason=entry_reason,
                result="PENDING",
                notes=json.dumps({
                    "conditions": conditions or {},
                    "tags": tags or [],
                }),
            )
            session.add(entry)
            session.commit()
            mem = TradeMemoryEntry(
                id=entry.id,
                symbol=entry.symbol,
                side=entry.side,
                entry_price=entry.entry_price,
                entry_reason=entry.entry_reason,
                conditions=conditions or {},
                tags=tags or [],
                created_at=entry.created_at.isoformat() if entry.created_at else None,
            )
            self._cache[entry.id] = mem
            return entry.id
        except Exception as e:
            session.rollback()
            logger.error("Failed to record trade memory: %s", e)
            return 0
        finally:
            session.close()

    def close(
        self,
        memory_id: int,
        exit_price: float,
        pnl: float,
        result: str,
        exit_reason: Optional[str] = None,
        lessons: Optional[list[str]] = None,
    ) -> bool:
        """Close a trade memory entry with result and lessons."""
        session = self.session_factory()
        try:
            entry = session.query(JournalEntry).filter(JournalEntry.id == memory_id).first()
            if entry is None:
                logger.warning("Trade memory entry %s not found", memory_id)
                return False
            entry.exit_price = exit_price
            entry.pnl = pnl
            entry.result = result.upper()
            entry.exit_reason = exit_reason

            existing = json.loads(entry.notes) if entry.notes else {}
            existing["lessons"] = lessons or []
            existing["closed_at"] = datetime.now(timezone.utc).isoformat()
            entry.notes = json.dumps(existing)

            session.commit()

            if memory_id in self._cache:
                mem = self._cache[memory_id]
                mem.exit_price = exit_price
                mem.pnl = pnl
                mem.result = result.upper()
                mem.exit_reason = exit_reason
                mem.lessons = lessons or []

            return True
        except Exception as e:
            session.rollback()
            logger.error("Failed to close trade memory: %s", e)
            return False
        finally:
            session.close()

    def get(self, memory_id: int) -> Optional[TradeMemoryEntry]:
        """Get a trade memory entry by ID."""
        if memory_id in self._cache:
            return self._cache[memory_id]
        session = self.session_factory()
        try:
            entry = session.query(JournalEntry).filter(JournalEntry.id == memory_id).first()
            if entry is None:
                return None
            notes = json.loads(entry.notes) if entry.notes else {}
            mem = TradeMemoryEntry(
                id=entry.id,
                symbol=entry.symbol,
                side=entry.side,
                entry_price=entry.entry_price,
                exit_price=entry.exit_price,
                pnl=entry.pnl,
                result=entry.result,
                entry_reason=entry.entry_reason,
                exit_reason=entry.exit_reason,
                conditions=notes.get("conditions", {}),
                lessons=notes.get("lessons", []),
                tags=notes.get("tags", []),
                created_at=entry.created_at.isoformat() if entry.created_at else None,
            )
            self._cache[memory_id] = mem
            return mem
        finally:
            session.close()

    def list(self, limit: int = 50) -> list[TradeMemoryEntry]:
        """List recent trade memory entries."""
        session = self.session_factory()
        try:
            rows = session.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).all()
            result: list[TradeMemoryEntry] = []
            for row in rows:
                notes = json.loads(row.notes) if row.notes else {}
                result.append(TradeMemoryEntry(
                    id=row.id,
                    symbol=row.symbol,
                    side=row.side,
                    entry_price=row.entry_price,
                    exit_price=row.exit_price,
                    pnl=row.pnl,
                    result=row.result,
                    entry_reason=row.entry_reason,
                    exit_reason=row.exit_reason,
                    conditions=notes.get("conditions", {}),
                    lessons=notes.get("lessons", []),
                    tags=notes.get("tags", []),
                    created_at=row.created_at.isoformat() if row.created_at else None,
                ))
            return result
        finally:
            session.close()

    def stats(self) -> dict[str, Any]:
        """Compute aggregate statistics from trade memory."""
        entries = self.list(limit=1000)
        total = len(entries)
        wins = sum(1 for e in entries if e.result == "WIN")
        losses = sum(1 for e in entries if e.result == "LOSS")
        total_pnl = sum(e.pnl for e in entries)
        win_rate = (wins / total * 100) if total > 0 else 0

        most_common_tags: dict[str, int] = {}
        for e in entries:
            for tag in e.tags:
                most_common_tags[tag] = most_common_tags.get(tag, 0) + 1
        top_tags = sorted(most_common_tags.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_entries": total,
            "wins": wins,
            "losses": losses,
            "win_rate_pct": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
        }
