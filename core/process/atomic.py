# core/process/atomic.py
"""Atomic duration constraint tracking and yield point context / checks."""
from __future__ import annotations

import time
from typing import Optional


class AtomicDurationExceeded(Exception):
    """Raised when an execution exceeds its defined atomic duration without yielding."""
    pass


class YieldPoint:
    """Enforces atomic duration limit & yields execution when requested."""

    def __init__(self, atomic_limit_sec: float) -> None:
        self.atomic_limit_sec = atomic_limit_sec
        self.start_time: float = time.time()
        self._yield_requested: bool = False

    def reset(self) -> None:
        """Reset start time timer."""
        self.start_time = time.time()
        self._yield_requested = False

    def check_and_enforce(self) -> None:
        """Check elapsed time and raise an exception if atomic duration is exceeded."""
        elapsed = time.time() - self.start_time
        if elapsed > self.atomic_limit_sec:
            raise AtomicDurationExceeded(
                f"Atomic duration of {self.atomic_limit_sec}s exceeded (elapsed: {elapsed:.3f}s)"
            )

    @property
    def yield_requested(self) -> bool:
        return self._yield_requested

    def request_yield(self) -> None:
        self._yield_requested = True
