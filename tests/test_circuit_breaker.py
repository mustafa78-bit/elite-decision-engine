"""Deterministic tests for CircuitBreaker.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


class TestCircuitBreakerConstructor:

    def test_default_values(self):
        cb = CircuitBreaker()
        assert cb._failure_threshold == 5
        assert cb._recovery_timeout == 30.0
        assert cb.state == CircuitState.CLOSED

    def test_invalid_threshold(self):
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreaker(failure_threshold=0)

    def test_invalid_timeout(self):
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreaker(recovery_timeout=0)


class TestCircuitBreakerClosed:

    def test_call_succeeds(self):
        cb = CircuitBreaker()
        fn = MagicMock(return_value="ok")
        result = cb.call(fn)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_failure_increments_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        fn = MagicMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            cb.call(fn)
        assert cb._failure_count == 1
        assert cb.state == CircuitState.CLOSED

    def test_threshold_exceeded_opens_circuit(self):
        cb = CircuitBreaker(failure_threshold=3)
        fn = MagicMock(side_effect=ValueError("fail"))

        with pytest.raises(ValueError):
            cb.call(fn)
        assert cb.state == CircuitState.CLOSED

        with pytest.raises(ValueError):
            cb.call(fn)
        assert cb.state == CircuitState.CLOSED

        with pytest.raises(ValueError):
            cb.call(fn)
        assert cb.state == CircuitState.OPEN
        assert cb._failure_count == 3


class TestCircuitBreakerOpen:

    def test_open_blocks_requests(self):
        cb = CircuitBreaker(failure_threshold=1)
        fn = MagicMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            cb.call(fn)
        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerOpenError, match="OPEN"):
            cb.call(fn)

    def test_open_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        fn = MagicMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            cb.call(fn)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN


class TestCircuitBreakerHalfOpen:

    def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        fn_fail = MagicMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            cb.call(fn_fail)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        fn_ok = MagicMock(return_value="recovered")
        result = cb.call(fn_ok)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_half_open_failure_reopens_circuit(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        fn_fail = MagicMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            cb.call(fn_fail)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        with pytest.raises(ValueError):
            cb.call(fn_fail)
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerReset:

    def test_reset_clears_state(self):
        cb = CircuitBreaker(failure_threshold=2)
        fn = MagicMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            cb.call(fn)
        with pytest.raises(ValueError):
            cb.call(fn)
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

        fn_ok = MagicMock(return_value="ok")
        result = cb.call(fn_ok)
        assert result == "ok"


class TestCircuitBreakerStateProperty:

    def test_open_checks_timeout_on_read(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        with patch("core.circuit_breaker.CircuitBreaker._recovery_timeout_elapsed", return_value=True):
            cb._state = CircuitState.OPEN
            cb._last_failure_time = time.monotonic() - 100
            assert cb.state == CircuitState.HALF_OPEN

    def test_open_stays_open_before_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)
        with patch("core.circuit_breaker.CircuitBreaker._recovery_timeout_elapsed", return_value=False):
            cb._state = CircuitState.OPEN
            cb._last_failure_time = time.monotonic()
            assert cb.state == CircuitState.OPEN
