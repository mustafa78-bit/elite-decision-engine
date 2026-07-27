import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

from database import get_session
from memory.l0_event_log.service import L0EventStore
from memory.l0_event_log.models import NEXUSEvent
from memory.l1_views.models import ProjectionState
from memory.l1_views.base import BaseProjection
from memory.l1_views.registry import ProjectionRegistry, global_registry
from memory.l1_views.dispatcher import EventDispatcher

logger = logging.getLogger(__name__)


class ReplayCursor:
    """Manages progression tracking, sequential validation, and database-persisted checkpoints."""

    def __init__(self, projection_name: str, session_factory: Callable[[], Any] = get_session) -> None:
        self.projection_name = projection_name
        self.session_factory = session_factory

    def get_last_processed_seq_id(self) -> int:
        """Loads the persisted sequence ID checkpoint from the database."""
        session = self.session_factory()
        try:
            state = session.query(ProjectionState).filter(ProjectionState.projection_name == self.projection_name).first()
            return state.last_processed_seq_id if state else 0
        finally:
            session.close()

    def update_checkpoint(
        self,
        seq_id: Optional[int] = None,
        replay_cursor: Optional[Dict[str, Any]] = None,
        rebuild_status: str = "COMPLETED",
        health_status: str = "HEALTHY",
        last_error: Optional[str] = None,
    ) -> None:
        """Persists the progress sequence ID and cursor info directly into the database."""
        session = self.session_factory()
        try:
            state = session.query(ProjectionState).filter(ProjectionState.projection_name == self.projection_name).first()
            if not state:
                state = ProjectionState(
                    projection_name=self.projection_name,
                    last_processed_seq_id=seq_id if seq_id is not None else 0,
                    replay_cursor=replay_cursor or {},
                    rebuild_status=rebuild_status,
                    health_status=health_status,
                    last_error=last_error,
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(state)
            else:
                if seq_id is not None:
                    state.last_processed_seq_id = seq_id
                state.replay_cursor = replay_cursor if replay_cursor is not None else state.replay_cursor
                state.rebuild_status = rebuild_status
                state.health_status = health_status
                state.last_error = last_error
                state.updated_at = datetime.now(timezone.utc)

            session.commit()
            logger.debug("Persisted L1 checkpoint for '%s' at seq_id: %s", self.projection_name, seq_id)
        except Exception as e:
            session.rollback()
            logger.error("Failed to persist L1 checkpoint for '%s': %s", self.projection_name, e)
            raise
        finally:
            session.close()

    def validate_sequence(self, event: NEXUSEvent) -> bool:
        """Ensures that the event sequence is monotonic and strictly progressing.

        Returns True if valid, False if it is a duplicate/older event.
        """
        last_seq = self.get_last_processed_seq_id()
        if event.seq_id <= last_seq:
            logger.debug(
                "Event seq_id (%d) <= last processed seq_id (%d) for '%s'. Skipping.",
                event.seq_id,
                last_seq,
                self.projection_name,
            )
            return False
        return True


class ProjectionRunner:
    """Orchestrates L1 projection execution, including rebuilds, incremental replays,

    snapshot restoration, retry handling, and metrics collection.
    """

    def __init__(
        self,
        registry: Optional[ProjectionRegistry] = None,
        dispatcher: Optional[EventDispatcher] = None,
        event_store: Optional[L0EventStore] = None,
        session_factory: Callable[[], Any] = get_session,
    ) -> None:
        self.registry = registry or global_registry
        self.dispatcher = dispatcher or EventDispatcher(registry=self.registry)
        self.event_store = event_store or L0EventStore(session_factory=session_factory)
        self.session_factory = session_factory

        # Orchestration metrics
        self.processed_events = 0
        self.failed_events = 0
        self.retry_count = 0
        self.rebuild_duration = 0.0
        self.replay_speed = 0.0

        logger.info("ProjectionRunner initialized.")

    def get_max_l0_seq_id(self) -> int:
        """Gets the maximum sequence ID present in L0 Event Store."""
        session = self.session_factory()
        try:
            max_seq = session.query(NEXUSEvent.seq_id).order_by(NEXUSEvent.seq_id.desc()).first()
            return max_seq[0] if max_seq else 0
        finally:
            session.close()

    def get_replay_lag(self) -> int:
        """Calculates the maximum replay lag across all registered projections."""
        max_l0 = self.get_max_l0_seq_id()
        projections = self.registry.list_projections()
        if not projections:
            return 0

        max_lag = 0
        for p in projections:
            cursor = ReplayCursor(p.projection_name, session_factory=self.session_factory)
            last_seq = cursor.get_last_processed_seq_id()
            max_lag = max(max_lag, max(0, max_l0 - last_seq))

        return max_lag

    def get_metrics(self) -> Dict[str, Any]:
        """Collects and returns generic projection performance and execution metrics."""
        lag = self.get_replay_lag()
        return {
            "replay_speed": self.replay_speed,
            "processed_events": self.processed_events,
            "replay_lag": lag,
            "failed_events": self.failed_events,
            "retry_count": self.retry_count,
            "rebuild_duration": self.rebuild_duration,
            "active_projection_count": len(self.registry.list_projections()),
        }

    def reset_metrics(self) -> None:
        """Resets run-time metrics."""
        self.processed_events = 0
        self.failed_events = 0
        self.retry_count = 0
        self.rebuild_duration = 0.0
        self.replay_speed = 0.0

    def rebuild_projection(self, projection_name: str) -> Dict[str, Any]:
        """Executes a full clean-rebuild of a single registered projection.

        This calls rebuild on the projection, resets its DB cursor to 0, and replays all events from 0.
        """
        self.reset_metrics()
        start_time = time.perf_counter()

        projection = self.registry.get_by_name(projection_name)
        if not projection:
            raise ValueError(f"Projection '{projection_name}' is not registered.")

        # Set DB state to RUNNING rebuild
        cursor = ReplayCursor(projection_name, session_factory=self.session_factory)
        cursor.update_checkpoint(seq_id=0, rebuild_status="RUNNING")

        # Clear state
        try:
            projection.rebuild()
        except Exception as e:
            cursor.update_checkpoint(seq_id=0, rebuild_status="FAILED", health_status="FAILED", last_error=str(e))
            raise

        # Replay all events from seq_id = 1
        res = self.replay_projection(projection_name=projection_name, start_seq_id=1)

        self.rebuild_duration = time.perf_counter() - start_time
        if self.rebuild_duration > 0:
            self.replay_speed = self.processed_events / self.rebuild_duration

        cursor.update_checkpoint(seq_id=res["last_processed_seq_id"], rebuild_status="COMPLETED", health_status="HEALTHY")

        return {
            "projection_name": projection_name,
            "events_processed": res["events_processed"],
            "failed_events": res["failed_events"],
            "rebuild_duration": self.rebuild_duration,
            "replay_speed": self.replay_speed,
            "status": "COMPLETED",
        }

    def run_incremental_replay(self) -> Dict[str, Any]:
        """Runs incremental replay across all registered projections from their last checkpoints."""
        self.reset_metrics()
        start_time = time.perf_counter()

        projections = self.registry.list_projections()
        events_processed = 0
        failed_count = 0

        for p in projections:
            cursor = ReplayCursor(p.projection_name, session_factory=self.session_factory)
            last_seq = cursor.get_last_processed_seq_id()
            res = self.replay_projection(p.projection_name, start_seq_id=last_seq + 1)
            events_processed += res["events_processed"]
            failed_count += res["failed_events"]

        self.rebuild_duration = time.perf_counter() - start_time
        if self.rebuild_duration > 0:
            self.replay_speed = events_processed / self.rebuild_duration

        return {
            "events_processed": events_processed,
            "failed_events": failed_count,
            "rebuild_duration": self.rebuild_duration,
            "replay_speed": self.replay_speed,
        }

    def replay_projection(
        self,
        projection_name: str,
        start_seq_id: int,
        end_seq_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Streams and replays events for a specific projection in a given sequence range."""
        projection = self.registry.get_by_name(projection_name)
        if not projection:
            raise ValueError(f"Projection '{projection_name}' is not registered.")

        cursor = ReplayCursor(projection_name, session_factory=self.session_factory)
        events_processed = 0
        failures = 0
        last_processed = cursor.get_last_processed_seq_id()

        # Stream events chronologically from start_seq_id
        session = self.session_factory()
        try:
            query = session.query(NEXUSEvent).filter(NEXUSEvent.seq_id >= start_seq_id)
            if end_seq_id is not None:
                query = query.filter(NEXUSEvent.seq_id <= end_seq_id)

            events = query.order_by(NEXUSEvent.seq_id.asc()).all()

            for event in events:
                # Validate event order / idempotency
                if not cursor.validate_sequence(event):
                    continue

                # Ensure projection supports the event type
                if event.event_type not in projection.supported_event_types():
                    continue

                # Process event with retry logic
                success = self._apply_with_retry(projection, cursor, event)
                if success:
                    events_processed += 1
                    last_processed = event.seq_id
                else:
                    failures += 1

            self.processed_events += events_processed
            self.failed_events += failures

            session.commit()
            return {
                "events_processed": events_processed,
                "failed_events": failures,
                "last_processed_seq_id": last_processed,
            }
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _apply_with_retry(
        self,
        projection: BaseProjection,
        cursor: ReplayCursor,
        event: NEXUSEvent,
        max_retries: int = 3,
    ) -> bool:
        """Applies an event to a projection, retrying on failure."""
        retries = 0
        while retries < max_retries:
            try:
                projection.apply(event)
                # Persist progress
                cursor.update_checkpoint(seq_id=event.seq_id)
                return True
            except Exception as e:
                retries += 1
                self.retry_count += 1
                logger.warning(
                    "Retry %d/%d for projection '%s' on event %d: %s",
                    retries,
                    max_retries,
                    projection.projection_name,
                    event.seq_id,
                    e,
                )
                time.sleep(0.02)  # short backoff

        logger.error(
            "Failed to apply event %d to projection '%s' after %d retries.",
            event.seq_id,
            projection.projection_name,
            max_retries,
        )
        cursor.update_checkpoint(
            rebuild_status="FAILED",
            health_status="DEGRADED",
            last_error=f"Failed on event {event.seq_id}",
        )
        return False

    def restore_projection_snapshot(self, projection_name: str, snapshot_state: Dict[str, Any], last_seq_id: int) -> None:
        """Restores a projection state from a serialized snapshot and updates its DB checkpoint."""
        projection = self.registry.get_by_name(projection_name)
        if not projection:
            raise ValueError(f"Projection '{projection_name}' is not registered.")

        # Restore in-memory state
        projection.restore_snapshot(snapshot_state)

        # Persist cursor checkpoint to state DB
        cursor = ReplayCursor(projection_name, session_factory=self.session_factory)
        cursor.update_checkpoint(
            seq_id=last_seq_id,
            replay_cursor={"snapshot_restored": True, "restored_at": datetime.now(timezone.utc).isoformat()},
        )
        logger.info(
            "Restored snapshot for projection '%s' at sequence ID %d",
            projection_name,
            last_seq_id,
        )
