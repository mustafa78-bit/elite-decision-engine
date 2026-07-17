from core.retry import RetryConfig, RetryHandler, with_retry


class TestRetryConfig:

    def test_defaults(self):
        cfg = RetryConfig()
        assert cfg.max_retries == 3
        assert cfg.base_delay == 1.0
        assert cfg.jitter is True


class TestRetryHandler:

    def test_execute_success(self):
        handler = RetryHandler(RetryConfig(max_retries=2, base_delay=0.01, jitter=False))
        result = handler.execute(lambda x: x + 1, 5)
        assert result == 6

    def test_execute_failure(self):
        handler = RetryHandler(RetryConfig(max_retries=1, base_delay=0.01, jitter=False))
        call_count = [0]

        def fails(x):
            call_count[0] += 1
            raise ValueError("always fails")

        import pytest
        with pytest.raises(ValueError):
            handler.execute(fails, 1)
        assert call_count[0] == 2

    def test_execute_succeeds_on_retry(self):
        handler = RetryHandler(RetryConfig(max_retries=2, base_delay=0.01, jitter=False))
        call_count = [0]

        def flaky(x):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("not yet")
            return x * 2

        result = handler.execute(flaky, 5)
        assert result == 10
        assert call_count[0] == 2


class TestWithRetry:

    def test_decorator(self):
        call_count = [0]

        @with_retry
        def works(x):
            call_count[0] += 1
            return x

        assert works(42) == 42
        assert call_count[0] == 1
