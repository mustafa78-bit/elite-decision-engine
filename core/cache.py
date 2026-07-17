import time
from threading import RLock
from typing import Any, Callable, Dict, Optional, Tuple


class TTLCache:

    def __init__(self, default_ttl: float = 60.0):
        self._default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = RLock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            value, expiry = self._store[key]
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
        with self._lock:
            self._store[key] = (value, expiry)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def cleanup(self) -> int:
        now = time.time()
        removed = 0
        with self._lock:
            stale = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in stale:
                del self._store[k]
                removed += 1
        return removed

    @property
    def size(self) -> int:
        with self._lock:
            self.cleanup()
            return len(self._store)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            self.cleanup()
            return {
                "size": len(self._store),
                "default_ttl": self._default_ttl,
                "keys": list(self._store.keys()),
            }


def cached(cache: TTLCache, ttl: Optional[float] = None):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
