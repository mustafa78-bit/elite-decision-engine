from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Callable, Optional


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")

        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self.logger = logger or logging.getLogger(__name__)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._recovery_timeout_elapsed():
            self.logger.info(
                "Circuit half-open after %.1fs timeout",
                self._recovery_timeout,
            )
            self._state = CircuitState.HALF_OPEN
        return self._state

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        current_state = self.state
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError("Circuit is OPEN — request blocked")

        try:
            result = fn(*args, **kwargs)
            if current_state == CircuitState.HALF_OPEN:
                self.logger.info(
                    "Circuit closed after successful half-open probe",
                )
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._last_failure_time = None
            return result
        except Exception as e:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if current_state == CircuitState.HALF_OPEN:
                self.logger.warning(
                    "Half-open probe failed — circuit open again",
                )
                self._state = CircuitState.OPEN

            if self._failure_count >= self._failure_threshold:
                self.logger.critical(
                    "Circuit opened after %s failures",
                    self._failure_count,
                )
                self._state = CircuitState.OPEN

            raise

    def _recovery_timeout_elapsed(self) -> bool:
        if self._last_failure_time is None:
            return True
        return (time.monotonic() - self._last_failure_time) >= self._recovery_timeout

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self.logger.info("Circuit manually reset to CLOSED")
