from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Set, Protocol, Optional
from services.intelligence.context import UnifiedIntelligenceContext

logger = logging.getLogger(__name__)


class IntelligenceServiceContract(Protocol):
    def get_service_name(self) -> str:
        """Returns the identifier name of the service."""
        ...

    def get_priority(self) -> int:
        """Returns the dynamic priority/weight of the service."""
        ...

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        """Executes the service cognitive/evaluation logic on the context."""
        ...


class CrossServiceEventBus:
    """A synchronous real-time event broker for cross-service communication."""

    def __init__(self):
        self._subscribers: Dict[str, Set[Callable[[Any, UnifiedIntelligenceContext], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any, UnifiedIntelligenceContext], None]) -> None:
        """Subscribes a callback handler to an event topic."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)
        logger.debug("Subscriber registered for event topic: %s", event_type)

    def unsubscribe(self, event_type: str, callback: Callable[[Any, UnifiedIntelligenceContext], None]) -> None:
        """Unsubscribes a callback handler from an event topic."""
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)
            logger.debug("Subscriber removed from event topic: %s", event_type)

    def publish(self, event_type: str, payload: Any, context: UnifiedIntelligenceContext) -> None:
        """Publishes an event payload to all topic subscribers synchronously."""
        subscribers = self._subscribers.get(event_type, set())
        if not subscribers:
            return

        logger.debug("Publishing topic '%s' to %d subscribers", event_type, len(subscribers))
        for callback in list(subscribers):
            try:
                callback(payload, context)
            except Exception as e:
                logger.error("Error invoking subscriber callback for topic '%s': %s", event_type, e, exc_info=True)


class PriorityResolver:
    """Computes deterministic and optimized execution priorities based on threat matrices & dependencies."""

    def __init__(self, override_priorities: Optional[Dict[str, int]] = None):
        self.override_priorities = override_priorities or {}

    def resolve(self, services: List[IntelligenceServiceContract]) -> List[IntelligenceServiceContract]:
        """Returns services sorted by their dynamic or configured priorities in descending order."""
        def get_resolved_priority(service: IntelligenceServiceContract) -> int:
            name = service.get_service_name()
            if name in self.override_priorities:
                return self.override_priorities[name]
            return service.get_priority()

        # Sort descending by priority, then lexicographically by name for deterministic order
        return sorted(services, key=lambda s: (get_resolved_priority(s), s.get_service_name()), reverse=True)
