from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from memory.l0_event_log.models import NEXUSEvent


class BaseProjection(ABC):
    """Abstract interface defining the complete lifecycle of every L1 Projection."""

    @property
    @abstractmethod
    def projection_name(self) -> str:
        """Returns the unique name of this projection."""
        pass

    @abstractmethod
    def supported_event_types(self) -> List[str]:
        """Returns a list of L0 event types that this projection subscribes to."""
        pass

    @abstractmethod
    def apply(self, event: NEXUSEvent) -> None:
        """Processes a single L0 event sequentially, updating the materialized projection."""
        pass

    @abstractmethod
    def rebuild(self) -> None:
        """Clears all materialized data for this projection to prepare for a full replay."""
        pass

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        """Captures a serializable state snapshot of the projection."""
        pass

    @abstractmethod
    def restore_snapshot(self, state: Dict[str, Any]) -> None:
        """Restores the projection state from a serialized snapshot."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validates the current materialized state against expected constraints/checksums."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Returns the health status and diagnostics metadata of the projection."""
        pass
