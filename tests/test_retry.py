"""Deterministic tests for RetryPolicy.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from core.retry import RetryPolicy


class _RetryableError(Exception):
    pass


class _NonRetryableError(Exception):
    pass


class TestRetryPolicyConstructor:

    def test_default_values(self):
        rp = RetryPolicy()
        assert rp._max_attempts == 4
        assert rp._base_delay == 1.0
        assert rp._max_delay == 60.0
        assert rp._backoff_multiplier == 2.0

    def test_invalid_max_attempts(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RetryPolicy(max_attempts=0)

    def test_invalid_base_delay(self):
        with pytest.raises(ValueError, match="base_delay"):
            RetryPolicy(base_delay=0)

    def test_invalid_max_delay(self):
        with pytest.raises(ValueError, match="max_delay"):
            RetryPolicy(base_delay=5.0, max_delay=2.0)

    def test_invalid_backoff_multiplier(self):
        with pytest.raises(ValueError, match="backoff_multiplier"):
            RetryPolicy(backoff_multiplier=1.0)


class TestRetryPolicyExecute:

    def test_succeeds_on_first_attempt(self):
        rp = RetryPolicy(max_attempts=3)
        fn = MagicMock(return_value="ok")
        result = rp.execute(fn)
        assert result == "ok"
        fn.assert_called_once()

    def test_retry_succeeds_after_failures(self):
        fn = MagicMock()
        fn.side_effect = [
            _RetryableError("fail 1"),
            _RetryableError("fail 2"),
            "success",
        ]
        rp = RetryPolicy(
            max_attempts=4,
            base_delay=0.01,
            retry_exceptions=(_RetryableError,),
        )
        with patch("time.sleep"):
            result = rp.execute(fn)
        assert result == "success"
        assert fn.call_count == 3

    def test_retry_exhausted_raises(self):
        fn = MagicMock()
        fn.side_effect = _RetryableError("always fails")
        rp = RetryPolicy(
            max_attempts=3,
            base_delay=0.01,
            retry_exceptions=(_RetryableError,),
        )
        with patch("time.sleep"):
            with pytest.raises(_RetryableError):
                rp.execute(fn)
        assert fn.call_count == 3

    def test_non_retryable_exception_not_caught(self):
        fn = MagicMock(side_effect=_NonRetryableError("no retry"))
        rp = RetryPolicy(
            max_attempts=3,
            base_delay=0.01,
            retry_exceptions=(_RetryableError,),
        )
        with patch("time.sleep"):
            with pytest.raises(_NonRetryableError):
                rp.execute(fn)
        fn.assert_called_once()

    def test_backoff_sequence(self):
        fn = MagicMock()
        fn.side_effect = [
            _RetryableError("fail"),
            _RetryableError("fail"),
            _RetryableError("fail"),
            "ok",
        ]
        rp = RetryPolicy(
            max_attempts=4,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            retry_exceptions=(_RetryableError,),
        )
        with patch("time.sleep") as mock_sleep:
            rp.execute(fn)

        expected_delays = [1.0, 2.0, 4.0]
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_backoff_capped_at_max_delay(self):
        fn = MagicMock()
        fn.side_effect = [
            _RetryableError("fail"),
            _RetryableError("fail"),
            _RetryableError("fail"),
            _RetryableError("fail"),
            "ok",
        ]
        rp = RetryPolicy(
            max_attempts=5,
            base_delay=1.0,
            max_delay=3.0,
            backoff_multiplier=2.0,
            retry_exceptions=(_RetryableError,),
        )
        with patch("time.sleep") as mock_sleep:
            rp.execute(fn)

        expected_delays = [1.0, 2.0, 3.0, 3.0]
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_single_attempt_no_retry(self):
        fn = MagicMock(side_effect=_RetryableError("fail"))
        rp = RetryPolicy(
            max_attempts=1,
            retry_exceptions=(_RetryableError,),
        )
        with pytest.raises(_RetryableError):
            rp.execute(fn)
        fn.assert_called_once()

    def test_passes_args_and_kwargs(self):
        fn = MagicMock(return_value="ok")
        rp = RetryPolicy()
        rp.execute(fn, "arg1", key="val")
        fn.assert_called_once_with("arg1", key="val")
