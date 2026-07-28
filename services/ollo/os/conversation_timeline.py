from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TimelineEntry:
    """Strongly typed node on the NEXUS cognitive timeline."""

    conversation: str  # User prompt / discussion query
    intent: str  # Resolved intent / matched Tool
    decision: Dict[str, Any]  # DecisionResult / advice / output
    action: Optional[Dict[str, Any]] = None  # Executable command structure
    outcome: Optional[Dict[str, Any]] = None  # PnL, state transition, or results
    learning: Optional[List[str]] = None  # Learned patterns / identified mistakes
    signal_id: Optional[int] = None  # Link to the Decision Ledger (Signals)
    trade_id: Optional[int] = None  # Link to the Decision Ledger (Trades)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConversationTimeline:
    """Maintains the authoritative NEXUS Cognitive Timeline, linking conversations to Decisions, Actions, and Outcomes."""

    _instance: Optional[ConversationTimeline] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._entries: List[TimelineEntry] = []
        self._initialized = True

    def add_entry(
        self,
        conversation: str,
        intent: str,
        decision: Dict[str, Any],
        action: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        learning: Optional[List[str]] = None,
        signal_id: Optional[int] = None,
        trade_id: Optional[int] = None,
    ) -> TimelineEntry:
        """Create and append a new high-fidelity cognitive node to the timeline."""
        entry = TimelineEntry(
            conversation=conversation,
            intent=intent,
            decision=decision,
            action=action,
            outcome=outcome,
            learning=learning,
            signal_id=signal_id,
            trade_id=trade_id,
        )
        self._entries.append(entry)
        logger.info(
            "New Cognitive Timeline Entry: %s -> Intent: %s | Signal: %s",
            conversation[:30],
            intent,
            signal_id,
        )
        return entry

    def get_entries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent entries on the cognitive timeline."""
        return [e.to_dict() for e in self._entries[-limit:]]

    def get_by_signal_id(self, signal_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cognitive timeline node by signal ID (ledger link)."""
        for e in reversed(self._entries):
            if e.signal_id == signal_id:
                return e.to_dict()
        return None

    def clear(self) -> None:
        """Clear timeline entries."""
        self._entries.clear()
        logger.info("Cognitive timeline cleared.")


# Global singleton instance
conversation_timeline = ConversationTimeline()
