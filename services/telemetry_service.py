from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from database import TelemetryEvent, get_session

logger = logging.getLogger(__name__)


class TelemetryService:
    """Service to track and manage product telemetry events internally."""

    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def track_event(
        self,
        screen: str,
        action: str,
        duration: Optional[float] = None,
        outcome: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> TelemetryEvent:
        """Track and persist a single telemetry event."""
        if not screen or not action:
            raise ValueError("screen and action are required parameters")

        session = self.session_factory()
        try:
            event = TelemetryEvent(
                screen=screen.lower().strip(),
                action=action.lower().strip(),
                duration=duration,
                outcome=outcome.lower().strip() if outcome else None,
                timestamp=timestamp or datetime.now(timezone.utc),
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            logger.info("Telemetry event tracked: %s -> %s", event.screen, event.action)
            return event
        except Exception as e:
            session.rollback()
            logger.error("Failed to track telemetry event: %s", e)
            raise
        finally:
            session.close()

    def get_event_stream(self, limit: int = 100) -> list[TelemetryEvent]:
        """Fetch unified stream of telemetry events ordered by timestamp descending."""
        session = self.session_factory()
        try:
            return (
                session.query(TelemetryEvent)
                .order_by(TelemetryEvent.timestamp.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()
