"""Tests for CacheManager."""

import time
from market.cache import CacheManager


class TestCacheManager:

    def test_set_and_get(self):
        cache = CacheManager()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing(self):
        cache = CacheManager()
        assert cache.get("nonexistent") is None

    def test_expiry(self):
        cache = CacheManager(default_ttl=0.1)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.15)
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = CacheManager()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_clear(self):
        cache = CacheManager()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0

    def test_get_or_set(self):
        cache = CacheManager()
        called = 0

        def factory():
            nonlocal called
            called += 1
            return "computed"

        result1 = cache.get_or_set("key", factory)
        result2 = cache.get_or_set("key", factory)
        assert result1 == "computed"
        assert result2 == "computed"
        assert called == 1

    def test_invalidate_pattern(self):
        cache = CacheManager()
        cache.set("ohlcv:BTC:1h", "data1")
        cache.set("ohlcv:ETH:1h", "data2")
        cache.set("indicators:BTC", "data3")
        cache.invalidate_pattern("ohlcv:")
        assert cache.get("ohlcv:BTC:1h") is None
        assert cache.get("ohlcv:ETH:1h") is None
        assert cache.get("indicators:BTC") is not None

    def test_make_key(self):
        cache = CacheManager()
        assert cache.make_key("a", "b", "c") == "a:b:c"

    def test_custom_ttl_per_key(self):
        cache = CacheManager(default_ttl=60)
        cache.set("short", "value", ttl=0.1)
        cache.set("long", "value", ttl=60)
        time.sleep(0.15)
        assert cache.get("short") is None
        assert cache.get("long") == "value"
