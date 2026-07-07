from __future__ import annotations

import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class RetryPolicy:

    def __init__(
        self,
        max_attempts: int = 4,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        retry_exceptions: tuple[type[Exception], ...] = (
            ConnectionError,
            TimeoutError,
        ),
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if base_delay <= 0:
            raise ValueError("base_delay must be > 0")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if backoff_multiplier <= 1.0:
            raise ValueError("backoff_multiplier must be > 1.0")

        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._backoff_multiplier = backoff_multiplier
        self._retry_exceptions = retry_exceptions
        self.logger = logger or logging.getLogger(__name__)

    def execute(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        last_exception: Optional[Exception] = None
        delay = self._base_delay

        for attempt in range(1, self._max_attempts + 1):
            try:
                result = fn(*args, **kwargs)
                if attempt > 1:
                    self.logger.info(
                        "Retry attempt %s succeeded", attempt,
                    )
                return result
            except self._retry_exceptions as e:
                last_exception = e
                if attempt == self._max_attempts:
                    self.logger.error(
                        "Retry exhausted after %s attempts: %s",
                        self._max_attempts, e,
                    )
                    raise
                self.logger.warning(
                    "Temporary failure on attempt %s/%s: %s. Retrying in %.2fs",
                    attempt, self._max_attempts, e, delay,
                )
                time.sleep(delay)
                delay = min(delay * self._backoff_multiplier, self._max_delay)
