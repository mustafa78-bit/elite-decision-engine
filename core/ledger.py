from __future__ import annotations

import logging
from typing import Any, Optional

import database
from database import EventLedger

logger = logging.getLogger(__name__)


class LedgerService:
    """Append-only system ledger service."""

    def __init__(self, session_factory=None) -> None:
        self.session_factory = session_factory

    def _get_session(self):
        if self.session_factory is not None:
            return self.session_factory()
        return database.get_session()

    def append_event(
        self,
        event_type: str,
        symbol: Optional[str] = None,
        signal_id: Optional[int] = None,
        trade_id: Optional[int] = None,
        description: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> EventLedger:
        """Append a new event entry strictly in an append-only manner."""
        session = self._get_session()
        try:
            event = EventLedger(
                event_type=event_type,
                symbol=symbol.upper() if symbol else None,
                signal_id=signal_id,
                trade_id=trade_id,
                description=description,
                details=details or {},
            )
            session.add(event)
            session.commit()

            # Materialize all fields before session is closed/detached
            _ = event.id
            _ = event.event_type
            _ = event.symbol
            _ = event.signal_id
            _ = event.trade_id
            _ = event.description
            _ = event.details
            _ = event.timestamp

            logger.info(
                "[LEDGER] Appended event_type='%s' symbol='%s' signal_id=%s trade_id=%s",
                event_type, symbol, signal_id, trade_id,
            )
            return event
        except Exception as e:
            session.rollback()
            logger.error("Failed to append event to Ledger: %s", e)
            raise e
        finally:
            session.close()

    def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> list[EventLedger]:
        """Query ledger events chronologically with support for filtering."""
        session = self._get_session()
        try:
            query = session.query(EventLedger)
            if event_type:
                query = query.filter(EventLedger.event_type == event_type)
            if symbol:
                query = query.filter(EventLedger.symbol == symbol.upper())

            # Sort newest first
            return query.order_by(EventLedger.timestamp.desc()).offset(offset).limit(limit).all()
        finally:
            session.close()

    def get_signal_events(self, signal_id: int) -> list[EventLedger]:
        """Retrieve all events corresponding to a signal."""
        session = self._get_session()
        try:
            return (
                session.query(EventLedger)
                .filter(EventLedger.signal_id == signal_id)
                .order_by(EventLedger.timestamp.asc())
                .all()
            )
        finally:
            session.close()

    def get_trade_events(self, trade_id: int) -> list[EventLedger]:
        """Retrieve all events corresponding to a trade."""
        session = self._get_session()
        try:
            return (
                session.query(EventLedger)
                .filter(EventLedger.trade_id == trade_id)
                .order_by(EventLedger.timestamp.asc())
                .all()
            )
        finally:
            session.close()
