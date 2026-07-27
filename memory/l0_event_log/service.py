from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from sqlalchemy import func
from database import get_session
from memory.l0_event_log.models import NEXUSEvent, NEXUSSnapshot

logger = logging.getLogger(__name__)


class L0EventStore:
    """Production-grade immutable L0 Event Store with cryptographic integrity checks,

    provenance preservation, event replay, state snapshots, streaming, and corruption detection.
    """

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self.session_factory = session_factory
        logger.info("L0 Immutable Event Store initialized.")

    def format_timestamp(self, dt: datetime) -> str:
        """Standardizes datetime representation to ensure consistent cryptographic checksums."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()

    def calculate_checksum(
        self,
        event_id: str,
        seq_id: int,
        timestamp_str: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> str:
        """Calculates a cryptographic SHA-256 hash signature of the event to enforce immutability.

        Formula: SHA256(event_id + seq_id + timestamp + event_type + JSON(payload))
        """
        payload_serialized = json.dumps(payload, sort_keys=True)
        raw_string = f"{event_id}{seq_id}{timestamp_str}{event_type}{payload_serialized}"
        return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()

    def _get_next_seq_id(self, session: Any) -> int:
        """Returns the next sequential ID in an atomic-like transaction block."""
        max_seq = session.query(func.max(NEXUSEvent.seq_id)).scalar()
        return (max_seq or 0) + 1

    def append(
        self,
        event_type: str,
        payload: Dict[str, Any],
        actor: Dict[str, str],
        causal_chain_id: str,
        parent_event_id: Optional[str] = None,
        sources: Optional[List[str]] = None,
        version: str = "1.0.0",
    ) -> NEXUSEvent:
        """Appends a single immutable event to the L0 Event Log with SHA-256 integrity signature."""
        session = self.session_factory()
        try:
            # 1. Provenance check: If parent_event_id is provided, verify it exists
            if parent_event_id:
                parent_exists = (
                    session.query(NEXUSEvent.event_id)
                    .filter(NEXUSEvent.event_id == parent_event_id)
                    .first()
                )
                if not parent_exists:
                    logger.warning(
                        "Provenance link warning: parent_event_id %s not found in L0 Event Log.",
                        parent_event_id,
                    )

            # 2. Assign next seq_id
            seq_id = self._get_next_seq_id(session)
            event_id = str(uuid.uuid4())
            now_utc = datetime.now(timezone.utc)
            timestamp_str = self.format_timestamp(now_utc)

            # 3. Calculate SHA-256 signature
            checksum = self.calculate_checksum(
                event_id=event_id,
                seq_id=seq_id,
                timestamp_str=timestamp_str,
                event_type=event_type,
                payload=payload,
            )

            # 4. Create and persist model
            event_model = NEXUSEvent(
                event_id=event_id,
                seq_id=seq_id,
                timestamp=now_utc,
                event_type=event_type,
                version=version,
                actor_id=actor.get("id", "unknown_actor"),
                actor_type=actor.get("type", "SYSTEM"),
                actor_name=actor.get("name", "Unknown Actor"),
                parent_event_id=parent_event_id,
                causal_chain_id=causal_chain_id,
                sources=sources or [],
                payload=payload,
                checksum=checksum,
                is_quarantined=False,
            )

            session.add(event_model)
            session.commit()

            # Refresh and expunge to allow accessing properties safely outside the session
            session.refresh(event_model)
            session.expunge(event_model)

            logger.info("Appended L0 Event: %s (Seq ID: %d)", event_id, seq_id)
            return event_model
        except Exception as e:
            session.rollback()
            logger.error("Failed to append event to L0 Event Log: %s", e)
            raise
        finally:
            session.close()

    def append_batch(
        self,
        events_data: List[Dict[str, Any]],
    ) -> List[NEXUSEvent]:
        """Appends a batch of immutable events to the L0 Event Log in a single transaction."""
        session = self.session_factory()
        persisted_events: List[NEXUSEvent] = []
        try:
            # Get start sequence ID for batch
            next_seq_id = self._get_next_seq_id(session)

            for idx, data in enumerate(events_data):
                event_id = str(uuid.uuid4())
                seq_id = next_seq_id + idx
                now_utc = datetime.now(timezone.utc)
                timestamp_str = self.format_timestamp(now_utc)

                payload = data.get("payload", {})
                event_type = data.get("event_type", "UNKNOWN_EVENT")

                checksum = self.calculate_checksum(
                    event_id=event_id,
                    seq_id=seq_id,
                    timestamp_str=timestamp_str,
                    event_type=event_type,
                    payload=payload,
                )

                actor = data.get("actor", {})
                event_model = NEXUSEvent(
                    event_id=event_id,
                    seq_id=seq_id,
                    timestamp=now_utc,
                    event_type=event_type,
                    version=data.get("version", "1.0.0"),
                    actor_id=actor.get("id", "unknown_actor"),
                    actor_type=actor.get("type", "SYSTEM"),
                    actor_name=actor.get("name", "Unknown Actor"),
                    parent_event_id=data.get("parent_event_id"),
                    causal_chain_id=data.get("causal_chain_id", str(uuid.uuid4())),
                    sources=data.get("sources", []),
                    payload=payload,
                    checksum=checksum,
                    is_quarantined=False,
                )
                session.add(event_model)
                persisted_events.append(event_model)

            session.commit()

            # Refresh and expunge all models in the batch
            for model in persisted_events:
                session.refresh(model)
                session.expunge(model)

            logger.info("Batch appended %d L0 Events successfully.", len(persisted_events))
            return persisted_events
        except Exception as e:
            session.rollback()
            logger.error("Failed to append batch of events to L0 Event Log: %s", e)
            raise
        finally:
            session.close()

    def get_event(self, event_id: str) -> Optional[NEXUSEvent]:
        """Retrieves a single L0 Event by its UUID."""
        session = self.session_factory()
        try:
            event = session.query(NEXUSEvent).filter(NEXUSEvent.event_id == event_id).first()
            if event:
                session.refresh(event)
                session.expunge(event)
            return event
        finally:
            session.close()

    def read_events(
        self,
        start_seq_id: Optional[int] = None,
        end_seq_id: Optional[int] = None,
        causal_chain_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_quarantined: bool = False,
    ) -> List[NEXUSEvent]:
        """Reads a list of events with customizable filters and sequence range limits."""
        session = self.session_factory()
        try:
            query = session.query(NEXUSEvent)

            if not include_quarantined:
                query = query.filter(NEXUSEvent.is_quarantined == False)

            if start_seq_id is not None:
                query = query.filter(NEXUSEvent.seq_id >= start_seq_id)
            if end_seq_id is not None:
                query = query.filter(NEXUSEvent.seq_id <= end_seq_id)
            if causal_chain_id is not None:
                query = query.filter(NEXUSEvent.causal_chain_id == causal_chain_id)
            if event_type is not None:
                query = query.filter(NEXUSEvent.event_type == event_type)

            events = query.order_by(NEXUSEvent.seq_id.asc()).offset(offset).limit(limit).all()

            for event in events:
                session.refresh(event)
                session.expunge(event)

            return events
        finally:
            session.close()

    def stream_events(
        self,
        start_seq_id: int = 1,
        chunk_size: int = 50,
        include_quarantined: bool = False,
    ) -> Generator[NEXUSEvent, None, None]:
        """Streams events sequentially in chunks to allow non-blocking event loop replay."""
        current_seq = start_seq_id
        while True:
            events = self.read_events(
                start_seq_id=current_seq,
                limit=chunk_size,
                include_quarantined=include_quarantined,
            )
            if not events:
                break
            for event in events:
                yield event
                current_seq = event.seq_id + 1

    def replay_events(
        self,
        causal_chain_id: str,
        up_to_seq_id: Optional[int] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        reducer: Optional[Callable[[Dict[str, Any], NEXUSEvent], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Replays events sequentially for a causal chain to reconstruct its state.

        Args:
            causal_chain_id: The UUID of the lineage causal chain.
            up_to_seq_id: Maximum sequence ID to play up to.
            initial_state: Optional base state to start applying event payload reducers.
            reducer: Optional function (state, event) -> state to apply state changes.
        """
        state = initial_state or {}
        events = self.read_events(
            causal_chain_id=causal_chain_id,
            end_seq_id=up_to_seq_id,
            include_quarantined=False,
        )

        if reducer:
            for event in events:
                state = reducer(state, event)
        else:
            # Default state reconstruction reducer: merge payloads
            for event in events:
                state.update(event.payload)

        return state

    def create_snapshot(
        self,
        causal_chain_id: str,
        last_seq_id: int,
        state: Dict[str, Any],
    ) -> NEXUSSnapshot:
        """Saves a state snapshot for a causal chain up to a specific seq_id to optimize replay."""
        session = self.session_factory()
        try:
            snapshot_id = str(uuid.uuid4())
            state_serialized = json.dumps(state, sort_keys=True)
            checksum = hashlib.sha256(state_serialized.encode("utf-8")).hexdigest()

            snapshot_model = NEXUSSnapshot(
                snapshot_id=snapshot_id,
                causal_chain_id=causal_chain_id,
                last_seq_id=last_seq_id,
                timestamp=datetime.now(timezone.utc),
                state=state,
                checksum=checksum,
            )

            session.add(snapshot_model)
            session.commit()

            session.refresh(snapshot_model)
            session.expunge(snapshot_model)

            logger.info("Saved state snapshot %s for causal chain %s", snapshot_id, causal_chain_id)
            return snapshot_model
        except Exception as e:
            session.rollback()
            logger.error("Failed to create state snapshot: %s", e)
            raise
        finally:
            session.close()

    def get_latest_snapshot(self, causal_chain_id: str) -> Optional[NEXUSSnapshot]:
        """Retrieves the latest state snapshot for a causal chain."""
        session = self.session_factory()
        try:
            snapshot = (
                session.query(NEXUSSnapshot)
                .filter(NEXUSSnapshot.causal_chain_id == causal_chain_id)
                .order_by(NEXUSSnapshot.last_seq_id.desc())
                .first()
            )
            if snapshot:
                session.refresh(snapshot)
                session.expunge(snapshot)
            return snapshot
        finally:
            session.close()

    def verify_integrity(self) -> Tuple[List[str], List[str]]:
        """Scans the entire event log to verify SHA-256 checksum signatures.

        Automatically quarantine corrupted/modified events to prevent state drift.

        Returns:
            A tuple of (corrupted_event_ids, quarantined_event_ids).
        """
        session = self.session_factory()
        corrupted: List[str] = []
        quarantined: List[str] = []
        try:
            # Read all non-quarantined events
            events = session.query(NEXUSEvent).filter(NEXUSEvent.is_quarantined == False).all()

            for event in events:
                timestamp_str = self.format_timestamp(event.timestamp)
                computed = self.calculate_checksum(
                    event_id=event.event_id,
                    seq_id=event.seq_id,
                    timestamp_str=timestamp_str,
                    event_type=event.event_type,
                    payload=event.payload,
                )

                if computed != event.checksum:
                    logger.critical(
                        "CORRUPTION DETECTED: L0 Event %s (Seq ID: %d) has mismatched checksum!",
                        event.event_id,
                        event.seq_id,
                    )
                    corrupted.append(event.event_id)

                    # Quarantine the corrupted event
                    event.is_quarantined = True
                    event.quarantine_reason = (
                        f"Checksum mismatch on {datetime.now(timezone.utc).isoformat()}. "
                        f"Expected {event.checksum}, got {computed}."
                    )
                    quarantined.append(event.event_id)

            if quarantined:
                session.commit()
                logger.warning("Quarantined %d corrupted L0 Event(s).", len(quarantined))

            return corrupted, quarantined
        except Exception as e:
            session.rollback()
            logger.error("Integrity verification failed: %s", e)
            raise
        finally:
            session.close()
