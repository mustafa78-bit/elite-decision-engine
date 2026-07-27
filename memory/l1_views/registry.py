import logging
from typing import Dict, List, Optional, Type
from memory.l1_views.base import BaseProjection

logger = logging.getLogger(__name__)


class ProjectionRegistry:
    """Manages L1 materialized view projections dynamically and provides lookup indexes."""

    def __init__(self) -> None:
        self._projections: Dict[str, BaseProjection] = {}
        # Index: event_type -> list of projections subscribed to it
        self._event_type_index: Dict[str, List[BaseProjection]] = {}
        logger.info("ProjectionRegistry initialized.")

    def register(self, projection: BaseProjection) -> None:
        """Dynamically registers a unique projection.

        Raises:
            ValueError: If a projection with the same name already exists.
        """
        name = projection.projection_name
        if not name:
            raise ValueError("Projection name cannot be empty.")

        if name in self._projections:
            raise ValueError(f"Duplicate registration detected: Projection '{name}' is already registered.")

        self._projections[name] = projection

        # Update event type index
        event_types = projection.supported_event_types()
        for et in event_types:
            if et not in self._event_type_index:
                self._event_type_index[et] = []
            self._event_type_index[et].append(projection)

        logger.info("Registered projection: %s (subscribes to %s)", name, event_types)

    def unregister(self, name: str) -> Optional[BaseProjection]:
        """Dynamically unregisters a projection by name. Useful for clean tests/plugins."""
        if name not in self._projections:
            return None

        projection = self._projections.pop(name)

        # Clean from event type index
        for et in list(self._event_type_index.keys()):
            self._event_type_index[et] = [p for p in self._event_type_index[et] if p.projection_name != name]
            if not self._event_type_index[et]:
                del self._event_type_index[et]

        logger.info("Unregistered projection: %s", name)
        return projection

    def get_by_name(self, name: str) -> Optional[BaseProjection]:
        """Looks up a registered projection by its unique name."""
        return self._projections.get(name)

    def get_by_event_type(self, event_type: str) -> List[BaseProjection]:
        """Looks up all registered projections interested in a given L0 event type."""
        return self._event_type_index.get(event_type, [])

    def list_projections(self) -> List[BaseProjection]:
        """Lists all registered projections in the system."""
        return list(self._projections.values())

    def clear(self) -> None:
        """Clears all registrations. Primarily used for isolation in test suites."""
        self._projections.clear()
        self._event_type_index.clear()
        logger.info("Cleared all registered projections.")


# Global instance for dynamic module/plugin discovery
global_registry = ProjectionRegistry()
