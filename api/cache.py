from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class DashboardCache:
    def __init__(self, default_ttl: int = 30):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.time() - ts > self._default_ttl:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._cache[key] = (time.time(), value)

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


def invalidate_dashboard_cache(pattern: Optional[str] = None) -> None:
    if pattern:
        keys = [k for k in _dashboard_cache._cache if pattern in k]
        for k in keys:
            _dashboard_cache.invalidate(k)
    else:
        _dashboard_cache.invalidate_all()
