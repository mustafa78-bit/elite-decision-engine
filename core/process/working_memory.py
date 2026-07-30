# core/process/working_memory.py
"""Working Memory ownership mapping with isolated process local scopes."""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class WorkingMemory:
    """Working Memory manages temporary, isolated process-local state."""

    def __init__(self, process_id: str) -> None:
        self.process_id = process_id
        self._store: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from process working memory."""
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in process working memory."""
        self._store[key] = value

    def clear(self) -> None:
        """Clear all process working memory."""
        self._store.clear()

    def get_all(self) -> Dict[str, Any]:
        """Retrieve a copy of all values in memory."""
        return dict(self._store)
