from __future__ import annotations

import logging
from typing import Any, Optional

import database
from database import EventLedger

logger = logging.getLogger(__name__)


class FounderTimelineService:
    """Project chronological Founder Activity stories directly from the Event Ledger."""

    def __init__(self, session_factory=None) -> None:
        self.session_factory = session_factory

    def _get_session(self):
        if self.session_factory is not None:
            return self.session_factory()
        return database.get_session()

    def get_founder_timeline(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """Build a high-density, chronological narrative sequence of Founder actions derived from the Ledger."""
        session = self._get_session()
        try:
            # Group events by signal_id to form cohesive narrative sequences
            # Let's query all ledger events
            events = (
                session.query(EventLedger)
                .order_by(EventLedger.timestamp.asc())
                .all()
            )

            # Group events by signal_id
            sequences: dict[int, list[EventLedger]] = {}
            for event in events:
                if event.signal_id is not None:
                    if event.signal_id not in sequences:
                        sequences[event.signal_id] = []
                    sequences[event.signal_id].append(event)

            narratives = []
            for sig_id, seq in sequences.items():
                story: dict[str, Any] = {
                    "signal_id": sig_id,
                    "symbol": None,
                    "timestamp": None,
                    "analyzed": None,
                    "decision_made": None,
                    "action_followed": None,
                    "afterwards": None,
                }

                # Find symbol and initial timestamp
                for event in seq:
                    if event.symbol:
                        story["symbol"] = event.symbol
                    if story["timestamp"] is None and event.timestamp:
                        story["timestamp"] = event.timestamp.isoformat()

                # Build the 4-phase narrative derived from the Ledger
                for event in seq:
                    ev_type = event.event_type
                    details = event.details or {}

                    if ev_type == "Signal Created":
                        story["analyzed"] = {
                            "description": event.description,
                            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                            "details": details,
                        }
                    elif ev_type == "Decision Generated":
                        story["decision_made"] = {
                            "description": event.description,
                            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                            "decision": details.get("decision"),
                            "confidence": details.get("confidence"),
                            "reasoning": details.get("reasoning"),
                        }
                    elif ev_type in ("Risk Evaluation", "Trade Executed"):
                        # If we have both, combine or use Trade Executed as the ultimate action
                        if story["action_followed"] is None or ev_type == "Trade Executed":
                            story["action_followed"] = {
                                "description": event.description,
                                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                                "details": details,
                            }
                    elif ev_type in ("Trade Closed", "Outcome Calculated", "Feedback Stored"):
                        # Combine or updatewards with the terminal outcome
                        if story["afterwards"] is None or ev_type == "Outcome Calculated":
                            story["afterwards"] = {
                                "description": event.description,
                                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                                "details": details,
                            }

                # Only include stories that have at least some components
                if story["analyzed"] or story["decision_made"] or story["action_followed"] or story["afterwards"]:
                    narratives.append(story)

            # Sort narratives newest first
            narratives.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
            return narratives[offset:offset + limit]

        finally:
            session.close()
