"""Single cache for all market data — no duplicated API calls."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 60  # seconds


class CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl

    @property
    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class CacheManager:
    """Thread-safe in-memory cache with per-key TTL."""

    def __init__(self, default_ttl: float = _DEFAULT_TTL) -> None:
        self._default_ttl = default_ttl
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            self._evict(key)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        with self._lock:
            self._store[key] = CacheEntry(value, ttl if ttl is not None else self._default_ttl)

    def get_or_set(self, key: str, factory, ttl: Optional[float] = None) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = factory()
        self.set(key, value, ttl)
        return value

    def invalidate(self, key: str) -> None:
        self._evict(key)

    def invalidate_pattern(self, prefix: str) -> None:
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def _evict(self, key: str) -> None:
        self._store.pop(key, None)

    @property
    def size(self) -> int:
        return len(self._store)

    def make_key(self, *parts: str) -> str:
        return ":".join(parts)
