import time
import random
from typing import Any, Callable, Optional, Type


class RetryConfig:

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


def with_retry(
    func: Callable,
    config: Optional[RetryConfig] = None,
    exceptions: Optional[tuple] = None,
) -> Callable:
    cfg = config or RetryConfig()
    exc_types = exceptions or (Exception,)

    def wrapper(*args, **kwargs) -> Any:
        last_exc = None
        for attempt in range(cfg.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exc_types as e:
                last_exc = e
                if attempt < cfg.max_retries:
                    delay = min(cfg.base_delay * (cfg.backoff_factor ** attempt), cfg.max_delay)
                    if cfg.jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    time.sleep(delay)
        raise last_exc

    return wrapper


class RetryHandler:

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        return with_retry(func, self.config)(*args, **kwargs)
