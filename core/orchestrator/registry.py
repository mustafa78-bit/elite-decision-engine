from __future__ import annotations

import logging
from typing import Any, Callable, Dict
from core.orchestrator.models import IntelligenceContext, IntelligenceResult

logger = logging.getLogger(__name__)


class IntelligenceRegistry:
    """Pluggable registry mapping engine capability names to their execution handlers."""

    def __init__(self):
        self._handlers: Dict[str, Callable[[IntelligenceContext], IntelligenceResult]] = {}

    def register(self, capability: str, handler: Callable[[IntelligenceContext], IntelligenceResult]) -> None:
        """Register a handler for a given capability stage."""
        self._handlers[capability] = handler
        logger.info("[Registry] Registered handler for stage capability: %s", capability)

    def get_handler(self, capability: str) -> Callable[[IntelligenceContext], IntelligenceResult]:
        """Fetch the registered handler for a capability stage."""
        if capability not in self._handlers:
            raise KeyError(f"No intelligence handler registered for capability stage: {capability}")
        return self._handlers[capability]

    def has_handler(self, capability: str) -> bool:
        """Check if capability handler exists."""
        return capability in self._handlers

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()


# Global Singleton instance for capability mapping
intelligence_registry = IntelligenceRegistry()
