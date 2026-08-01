"""Tests for feature store."""

import time

from features.store import FeatureStore


class TestFeatureStore:
    def test_set_and_get(self):
        fs = FeatureStore()
        fs.set("BTC", "rsi", 65.0)
        assert fs.get("BTC", "rsi") == 65.0

    def test_get_missing(self):
        fs = FeatureStore()
        assert fs.get("BTC", "nonexistent") is None

    def test_case_insensitive_symbol(self):
        fs = FeatureStore()
        fs.set("btc", "price", 50000)
        assert fs.get("BTC", "price") == 50000

    def test_ttl_expiry(self):
        fs = FeatureStore()
        fs.set("BTC", "volatility", 0.05, ttl=0.1)
        assert fs.get("BTC", "volatility") == 0.05
        time.sleep(0.15)
        assert fs.get("BTC", "volatility") is None

    def test_set_batch(self):
        fs = FeatureStore()
        fs.set_batch("ETH", {"rsi": 45, "ema20": 3000, "volume": 1000000})
        assert fs.get("ETH", "rsi") == 45
        assert fs.get("ETH", "ema20") == 3000
        assert fs.get("ETH", "volume") == 1000000

    def test_get_all(self):
        fs = FeatureStore()
        fs.set("BTC", "rsi", 60)
        fs.set("BTC", "price", 50000)
        fs.set("ETH", "price", 3000)
        all_btc = fs.get_all("BTC")
        assert "rsi" in all_btc
        assert "price" in all_btc
        assert all_btc["rsi"] == 60
        all_eth = fs.get_all("ETH")
        assert "price" in all_eth
        assert "rsi" not in all_eth

    def test_delete(self):
        fs = FeatureStore()
        fs.set("BTC", "rsi", 70)
        assert fs.delete("BTC", "rsi") is True
        assert fs.get("BTC", "rsi") is None
        assert fs.delete("BTC", "rsi") is False

    def test_clear_symbol(self):
        fs = FeatureStore()
        fs.set("BTC", "rsi", 50)
        fs.set("ETH", "rsi", 60)
        assert fs.clear("BTC") == 1
        assert fs.count() == 1

    def test_clear_all(self):
        fs = FeatureStore()
        fs.set("BTC", "a", 1)
        fs.set("ETH", "b", 2)
        assert fs.clear() == 2
        assert fs.count() == 0

    def test_snapshot(self):
        fs = FeatureStore()
        fs.set("BTC", "rsi", 55)
        snap = fs.snapshot("BTC")
        assert snap["symbol"] == "BTC"
        assert snap["feature_count"] == 1
        assert "rsi" in snap["features"]
