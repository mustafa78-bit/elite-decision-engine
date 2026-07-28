import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

from database import get_session
from memory.l0_event_log.models import NEXUSEvent
from memory.l1_views.base import BaseProjection
from memory.l1_views.models import WhaleView

logger = logging.getLogger(__name__)


class WhaleProjection(BaseProjection):
    """Production-grade Whale Projection mapping L0 events to WhaleView materialized records."""

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self.session_factory = session_factory

        # Metrics tracking
        self.processed_events = 0
        self.updated_whales = 0
        self.ignored_events = 0
        self.failed_updates = 0
        self.total_update_time = 0.0  # seconds

    @property
    def projection_name(self) -> str:
        return "WhaleProjection"

    def supported_event_types(self) -> List[str]:
        return ["WhaleActivity", "WhaleTransaction"]

    def apply(self, event: NEXUSEvent) -> None:
        """Applies a single L0 event sequentially to update affected fields on WhaleView."""
        event_type = event.event_type
        if event_type not in self.supported_event_types():
            self.ignored_events += 1
            return

        start_time = time.perf_counter()
        session = self.session_factory()
        try:
            payload = event.payload or {}
            wallet_id = payload.get("wallet_id") or payload.get("wallet")

            if not wallet_id:
                self.ignored_events += 1
                return

            whale = session.query(WhaleView).filter(WhaleView.wallet_id == wallet_id).first()
            is_new = False
            if not whale:
                is_new = True
                whale = WhaleView(
                    wallet_id=wallet_id,
                    total_events=0,
                    accumulation_score=0.0,
                    distribution_score=0.0,
                    realized_accuracy=0.0,
                    trust_score=0.0,
                    exchange_distribution={},
                    active_positions=[],
                    replay_seq_id=event.seq_id,
                    last_activity=event.timestamp,
                )
                session.add(whale)

            # Monotonic sequence check for idempotency
            if not is_new and event.seq_id <= whale.replay_seq_id:
                logger.debug(
                    "Duplicate/older event %s ignored for wallet %s in WhaleProjection.",
                    event.seq_id,
                    wallet_id,
                )
                return

            whale.total_events += 1
            whale.last_activity = event.timestamp

            # Event-specific logic
            if event_type == "WhaleActivity":
                if "accumulation_score" in payload and payload["accumulation_score"] is not None:
                    whale.accumulation_score = float(payload["accumulation_score"])
                if "distribution_score" in payload and payload["distribution_score"] is not None:
                    whale.distribution_score = float(payload["distribution_score"])
                if "trust_score" in payload and payload["trust_score"] is not None:
                    whale.trust_score = float(payload["trust_score"])
                if "exchange_distribution" in payload and payload["exchange_distribution"] is not None:
                    whale.exchange_distribution = payload["exchange_distribution"]

            elif event_type == "WhaleTransaction":
                if "realized_accuracy" in payload and payload["realized_accuracy"] is not None:
                    whale.realized_accuracy = float(payload["realized_accuracy"])
                pos = payload.get("position") or payload.get("asset")
                if pos:
                    active_pos = list(whale.active_positions or [])
                    action = payload.get("action", "BUY").upper()
                    if action == "BUY" and pos not in active_pos:
                        active_pos.append(pos)
                    elif action == "SELL" and pos in active_pos:
                        active_pos.remove(pos)
                    whale.active_positions = active_pos

            whale.replay_seq_id = event.seq_id
            self.updated_whales += 1

            session.commit()
            self.processed_events += 1
            self.total_update_time += (time.perf_counter() - start_time)
        except Exception as e:
            session.rollback()
            self.failed_updates += 1
            logger.error("Failed to apply event to WhaleProjection: %s", e)
            raise
        finally:
            session.close()

    def rebuild(self) -> None:
        """Clears all materialized data in l1_whale_views and resets projection metrics."""
        session = self.session_factory()
        try:
            session.query(WhaleView).delete()
            session.commit()

            self.processed_events = 0
            self.updated_whales = 0
            self.ignored_events = 0
            self.failed_updates = 0
            self.total_update_time = 0.0
            logger.info("WhaleProjection rebuilt successfully.")
        except Exception as e:
            session.rollback()
            logger.error("Failed to rebuild WhaleProjection: %s", e)
            raise
        finally:
            session.close()

    def snapshot(self) -> Dict[str, Any]:
        """Captures a serializable snapshot state of the WhaleProjection."""
        session = self.session_factory()
        try:
            whales = session.query(WhaleView).all()
            return {
                "whales": [
                    {
                        "wallet_id": w.wallet_id,
                        "total_events": w.total_events,
                        "accumulation_score": w.accumulation_score,
                        "distribution_score": w.distribution_score,
                        "realized_accuracy": w.realized_accuracy,
                        "trust_score": w.trust_score,
                        "last_activity": w.last_activity.isoformat() if w.last_activity else None,
                        "exchange_distribution": w.exchange_distribution,
                        "active_positions": w.active_positions,
                        "replay_seq_id": w.replay_seq_id,
                    }
                    for w in whales
                ]
            }
        finally:
            session.close()

    def restore_snapshot(self, state: Dict[str, Any]) -> None:
        """Restores the WhaleView table from the serialized snapshot state."""
        session = self.session_factory()
        try:
            session.query(WhaleView).delete()

            for data in state.get("whales", []):
                last_act = None
                if data.get("last_activity"):
                    last_act = datetime.fromisoformat(data["last_activity"])

                whale = WhaleView(
                    wallet_id=data["wallet_id"],
                    total_events=data["total_events"],
                    accumulation_score=data["accumulation_score"],
                    distribution_score=data["distribution_score"],
                    realized_accuracy=data["realized_accuracy"],
                    trust_score=data["trust_score"],
                    last_activity=last_act,
                    exchange_distribution=data["exchange_distribution"],
                    active_positions=data["active_positions"],
                    replay_seq_id=data["replay_seq_id"],
                )
                session.add(whale)

            session.commit()
            logger.info("WhaleProjection snapshot restored successfully with %d whales.", len(state.get("whales", [])))
        except Exception as e:
            session.rollback()
            logger.error("Failed to restore WhaleProjection snapshot: %s", e)
            raise
        finally:
            session.close()

    def validate(self) -> bool:
        """Validates current database entries against constraints."""
        session = self.session_factory()
        try:
            whales = session.query(WhaleView).all()
            for w in whales:
                if not w.wallet_id or len(w.wallet_id) > 100:
                    return False
                if w.total_events < 0:
                    return False
            return True
        except Exception:
            return False
        finally:
            session.close()

    def health(self) -> Dict[str, Any]:
        """Returns health diagnostics and tracking metrics."""
        avg_latency = 0.0
        if self.processed_events > 0:
            avg_latency = self.total_update_time / self.processed_events

        return {
            "status": "HEALTHY" if self.failed_updates == 0 else "DEGRADED",
            "processed_events": self.processed_events,
            "updated_whales": self.updated_whales,
            "ignored_events": self.ignored_events,
            "failed_updates": self.failed_updates,
            "average_update_latency": avg_latency,
        }
