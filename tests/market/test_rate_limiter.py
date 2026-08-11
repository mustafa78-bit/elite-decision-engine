"""Tests for TokenBucketRateLimiter."""

import threading
import time

import pytest

from market.provider.rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter:

    def test_rejects_non_positive_rate(self):
        with pytest.raises(ValueError):
            TokenBucketRateLimiter(0)
        with pytest.raises(ValueError):
            TokenBucketRateLimiter(-1)

    def test_first_burst_up_to_capacity_does_not_block(self):
        limiter = TokenBucketRateLimiter(tokens_per_second=10, burst_size=5)
        start = time.monotonic()
        for _ in range(5):
            limiter.acquire()
        elapsed = time.monotonic() - start
        # 5 tokens available immediately (starts full) -- should be near-instant.
        assert elapsed < 0.2

    def test_exceeding_burst_capacity_blocks_and_stays_under_rate(self):
        rate = 20.0  # 20 tokens/sec == one token every 50ms
        limiter = TokenBucketRateLimiter(tokens_per_second=rate, burst_size=1)
        # First acquire is free (bucket starts full), remaining 4 must each
        # wait ~1/rate seconds -- assert real outbound call *rate*, not just
        # that every call eventually succeeds.
        start = time.monotonic()
        for _ in range(5):
            limiter.acquire()
        elapsed = time.monotonic() - start
        expected_min = 4 * (1.0 / rate)  # 4 waits after the first free token
        assert elapsed >= expected_min * 0.8  # small tolerance for scheduling jitter

    def test_concurrent_callers_stay_under_rate(self):
        rate = 20.0
        limiter = TokenBucketRateLimiter(tokens_per_second=rate, burst_size=1)
        call_count = 10
        timestamps: list[float] = []
        lock = threading.Lock()

        def worker():
            limiter.acquire()
            with lock:
                timestamps.append(time.monotonic())

        threads = [threading.Thread(target=worker) for _ in range(call_count)]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total_elapsed = timestamps[-1] - start
        # 10 calls at 20/sec with burst=1 must take at least ~9 * (1/20)s.
        expected_min = 9 * (1.0 / rate)
        assert total_elapsed >= expected_min * 0.8
        assert len(timestamps) == call_count
