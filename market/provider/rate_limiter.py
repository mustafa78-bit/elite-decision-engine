"""A simple thread-safe token-bucket rate limiter for synchronous HTTP providers.

Splitting the fixed 25-symbol universe across two providers (see multi.py) halves
average concurrent load per provider, but does not by itself guarantee staying
under either provider's real rate limit under bursty conditions -- several
subsystems can still poll the same provider at once. This limiter makes every
call sharing one instance wait its turn instead of firing unbounded concurrent
requests.
"""

from __future__ import annotations

import threading
import time


class TokenBucketRateLimiter:
    """Blocks the calling thread until a token is available, then consumes it.

    Refills at a constant rate (tokens_per_second), capped at burst_size so a
    long idle period doesn't let a caller fire an unbounded burst afterward.
    """

    def __init__(self, tokens_per_second: float, burst_size: int | None = None) -> None:
        if tokens_per_second <= 0:
            raise ValueError(f"tokens_per_second must be positive, got {tokens_per_second}")
        self._rate = tokens_per_second
        self._capacity = float(burst_size if burst_size is not None else max(1, int(tokens_per_second)))
        self._tokens = self._capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until one token is available, then consume it."""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._last_refill = now
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

                wait_time = (1.0 - self._tokens) / self._rate

            time.sleep(wait_time)
