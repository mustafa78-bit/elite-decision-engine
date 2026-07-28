import logging
import time
from typing import Dict, Any, List, Optional
from memory.l0_event_log.models import NEXUSEvent
from memory.l1_views.registry import ProjectionRegistry, global_registry

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Dispatches L0 events to registered projections interested in those event types.

    Preserves chronological event ordering and collects dispatch execution metrics.
    """

    def __init__(self, registry: Optional[ProjectionRegistry] = None) -> None:
        self.registry = registry or global_registry

        # Metrics
        self.processed_events = 0
        self.failed_events = 0
        self.retry_count = 0  # Collected from runner/apply retries if connected

        logger.info("EventDispatcher initialized.")

    def dispatch(self, event: NEXUSEvent) -> int:
        """Resolves interested projections and dispatches the event to them sequentially.

        Ensures event ordering and collects metrics. Does not mutate the event payload.

        Returns:
            The number of projections that processed the event.
        """
        event_type = event.event_type
        projections = self.registry.get_by_event_type(event_type)

        if not projections:
            logger.debug("No projections registered for event type: %s", event_type)
            return 0

        dispatched_count = 0
        for projection in projections:
            try:
                logger.debug(
                    "Dispatching event %s (Seq: %d) to projection %s",
                    event.event_id,
                    event.seq_id,
                    projection.projection_name,
                )
                projection.apply(event)
                dispatched_count += 1
            except Exception as e:
                self.failed_events += 1
                logger.error(
                    "Projection '%s' failed to process event %s (Seq: %d): %s",
                    projection.projection_name,
                    event.event_id,
                    event.seq_id,
                    e,
                    exc_info=True,
                )
                raise  # Raise so caller/runner can orchestrate transaction rollback/retries

        self.processed_events += 1
        return dispatched_count

    def get_metrics(self) -> Dict[str, Any]:
        """Exposes routing and dispatching metrics."""
        return {
            "processed_events": self.processed_events,
            "failed_events": self.failed_events,
            "retry_count": self.retry_count,
        }

    def reset_metrics(self) -> None:
        """Resets dispatcher performance metrics."""
        self.processed_events = 0
        self.failed_events = 0
        self.retry_count = 0
