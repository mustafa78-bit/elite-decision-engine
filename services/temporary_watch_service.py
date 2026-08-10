from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from database import TemporaryWatch, get_session

logger = logging.getLogger(__name__)

_DEFAULT_WINDOW_DAYS = 7


class TemporaryWatchService:
    def __init__(self, session_factory: Callable[[], Any] | None = None):
        self.session_factory = session_factory or get_session

    def add_symbol(
        self, symbol: str, days: int = _DEFAULT_WINDOW_DAYS, note: str | None = None
    ) -> dict[str, Any]:
        symbol = symbol.upper()
        expires_at = datetime.now(UTC) + timedelta(days=days)
        session = self.session_factory()
        try:
            # Upsert: re-adding an already-active symbol refreshes its
            # expiry instead of creating a duplicate row -- there's no
            # meaningful distinction between "still watching" and "watching
            # again", and a duplicate row would double-count the symbol in
            # active_symbols() (harmless post-dedup, but pointless row growth).
            row = (
                session.query(TemporaryWatch)
                .filter(TemporaryWatch.symbol == symbol, TemporaryWatch.expires_at > datetime.now(UTC))
                .first()
            )
            if row is not None:
                row.expires_at = expires_at
                if note is not None:
                    row.note = note
            else:
                row = TemporaryWatch(symbol=symbol, note=note, expires_at=expires_at)
                session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_dict(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_active(self) -> list[dict[str, Any]]:
        session = self.session_factory()
        try:
            rows = (
                session.query(TemporaryWatch)
                .filter(TemporaryWatch.expires_at > datetime.now(UTC))
                .order_by(TemporaryWatch.expires_at)
                .all()
            )
            return [self._to_dict(r) for r in rows]
        finally:
            session.close()

    def active_symbols(self) -> list[str]:
        session = self.session_factory()
        try:
            rows = (
                session.query(TemporaryWatch.symbol)
                .filter(TemporaryWatch.expires_at > datetime.now(UTC))
                .distinct()
                .all()
            )
            return [r[0] for r in rows]
        finally:
            session.close()

    def remove_symbol(self, symbol: str) -> bool:
        symbol = symbol.upper()
        session = self.session_factory()
        try:
            rows = session.query(TemporaryWatch).filter(TemporaryWatch.symbol == symbol).all()
            if not rows:
                return False
            for row in rows:
                session.delete(row)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _to_dict(self, row: TemporaryWatch) -> dict[str, Any]:
        return {
            "id": row.id,
            "symbol": row.symbol,
            "note": row.note,
            "added_at": row.added_at.isoformat() if row.added_at else None,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        }
