from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DashboardCache:
    def __init__(self, default_ttl: int = 30):
        self._cache: dict[str, tuple[float, Any, int]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value, ttl = entry
        if time.time() - ts > ttl:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._cache[key] = (time.time(), value, ttl if ttl is not None else self._default_ttl)

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def invalidate_all(self) -> None:
        self._cache.clear()


_dashboard_cache = DashboardCache()


def cached(ttl: int = 30):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached_val = _dashboard_cache.get(cache_key)
            if cached_val is not None:
                return cached_val
            result = func(*args, **kwargs)
            _dashboard_cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def invalidate_dashboard_cache(pattern: str | None = None) -> None:
    if pattern:
        keys = [k for k in _dashboard_cache._cache if pattern in k]
        for k in keys:
            _dashboard_cache.invalidate(k)
    else:
        _dashboard_cache.invalidate_all()
