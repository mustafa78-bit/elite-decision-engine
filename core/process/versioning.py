# core/process/versioning.py
"""Versioned optimistic concurrency tracker for state mutations."""
from __future__ import annotations

from typing import Any


class ConcurrentUpdateError(Exception):
    """Raised when an optimistic concurrency check fails."""
    pass


class VersionedState:
    """Helper wrapper to represent state that tracks modifications via a version integer."""

    def __init__(self, data: Any, version: int = 1) -> None:
        self._data = data
        self.version = version

    @property
    def data(self) -> Any:
        return self._data

    def mutate(self, new_data: Any, expected_version: int) -> None:
        """Mutate state if expected version matches, incrementing version."""
        if expected_version != self.version:
            raise ConcurrentUpdateError(
                f"Concurrency conflict: expected version {expected_version}, actual is {self.version}."
            )
        self._data = new_data
        self.version += 1
