from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from database import Watchlist, get_session

logger = logging.getLogger(__name__)


class WatchlistService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def list_watchlists(self, user_id: Optional[int] = None) -> list[dict[str, Any]]:
        session = self.session_factory()
        try:
            q = session.query(Watchlist)
            if user_id is not None:
                q = q.filter(Watchlist.user_id == user_id)
            rows = q.order_by(Watchlist.name).all()
            return [self._to_dict(r) for r in rows]
        finally:
            session.close()

    def get_watchlist(self, watchlist_id: int) -> Optional[dict[str, Any]]:
        session = self.session_factory()
        try:
            row = session.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
            return self._to_dict(row) if row else None
        finally:
            session.close()

    def create_watchlist(self, name: str, symbols: Optional[list[str]] = None, user_id: Optional[int] = None) -> dict[str, Any]:
        session = self.session_factory()
        try:
            row = Watchlist(name=name, symbols=symbols or [], user_id=user_id)
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_dict(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_watchlist(self, watchlist_id: int, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        session = self.session_factory()
        try:
            row = session.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
            if not row:
                return None
            if "name" in data:
                row.name = data["name"]
            if "symbols" in data:
                row.symbols = data["symbols"]
            if "add_symbols" in data:
                current = set(row.symbols or [])
                current.update(data["add_symbols"])
                row.symbols = list(current)
            if "remove_symbols" in data:
                current = set(row.symbols or [])
                current.difference_update(data["remove_symbols"])
                row.symbols = list(current)
            session.commit()
            session.refresh(row)
            return self._to_dict(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_watchlist(self, watchlist_id: int) -> bool:
        session = self.session_factory()
        try:
            row = session.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
            if not row:
                return False
            session.delete(row)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_symbol(self, watchlist_id: int, symbol: str) -> Optional[dict[str, Any]]:
        return self.update_watchlist(watchlist_id, {"add_symbols": [symbol]})

    def remove_symbol(self, watchlist_id: int, symbol: str) -> Optional[dict[str, Any]]:
        return self.update_watchlist(watchlist_id, {"remove_symbols": [symbol]})

    def _to_dict(self, row: Watchlist) -> dict[str, Any]:
        return {
            "id": row.id,
            "user_id": row.user_id,
            "name": row.name,
            "symbols": row.symbols or [],
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
