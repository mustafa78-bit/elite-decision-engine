# core/process/events.py
"""Process Scheduler event recording leveraging the existing system Event Store."""
from __future__ import annotations

import logging
from typing import Any, Optional

try:
    from core.ledger import LedgerService
except ImportError:
    class LedgerService:
        def __init__(self, session_factory=None) -> None:
            pass
        def append_event(self, **kwargs) -> Any:
            pass

logger = logging.getLogger(__name__)


class ProcessEventLogger:
    """Writers scheduler activity events directly to the system's EventLedger."""

    def __init__(self, ledger_service: Optional[LedgerService] = None) -> None:
        self.ledger = ledger_service or LedgerService()

    def record_process_event(
        self,
        event_type: str,
        process_id: str,
        description: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Append process activity to the EventLedger."""
        try:
            merged_details = details or {}
            merged_details["process_id"] = process_id
            self.ledger.append_event(
                event_type=event_type,
                description=description,
                details=merged_details,
            )
        except Exception as e:
            logger.error("Failed to append process event '%s' for %s: %s", event_type, process_id, e)
