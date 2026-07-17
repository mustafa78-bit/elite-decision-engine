import time
from core.cache import TTLCache, cached


class TestTTLCache:

    def test_set_and_get(self):
        cache = TTLCache(default_ttl=60)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_get_nonexistent(self):
        cache = TTLCache()
        assert cache.get("nonexistent") is None

    def test_expiry(self):
        cache = TTLCache(default_ttl=0.1)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.15)
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = TTLCache()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_clear(self):
        cache = TTLCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0

    def test_cleanup(self):
        cache = TTLCache(default_ttl=0.1)
        cache.set("a", 1)
        cache.set("b", 2)
        time.sleep(0.15)
        removed = cache.cleanup()
        assert removed == 2
        assert cache.size == 0

    def test_custom_ttl(self):
        cache = TTLCache(default_ttl=60)
        cache.set("key", "value", ttl=0.1)
        time.sleep(0.15)
        assert cache.get("key") is None

    def test_get_stats(self):
        cache = TTLCache(default_ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["default_ttl"] == 60
        assert "a" in stats["keys"]
        assert "b" in stats["keys"]


class TestCachedDecorator:

    def test_cached(self):
        cache = TTLCache(default_ttl=60)
        call_count = 0

        @cached(cache)
        def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive(5) == 10
        assert call_count == 1
        assert expensive(5) == 10
        assert call_count == 1
        assert expensive(7) == 14
        assert call_count == 2
