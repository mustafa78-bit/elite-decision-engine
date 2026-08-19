"""Tests for CandleStreamCache."""

import threading
import time
import pytest
import pandas as pd

from market.stream.cache import CandleStreamCache


def test_cache_initial_empty():
    cache = CandleStreamCache()
    assert cache.get("BTCUSDT", "1h") is None
    assert cache.get_last_updated("BTCUSDT", "1h") is None
    assert not cache.is_fresh("BTCUSDT", "1h", max_age_seconds=60)


def test_cache_update_and_get():
    cache = CandleStreamCache()
    candle1 = {
        "timestamp": 1600000000000,
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 102.0,
        "volume": 10.5,
    }
    cache.update("BTCUSDT", "1h", candle1)

    df = cache.get("BTCUSDT", "1h")
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert df.iloc[0]["timestamp"] == 1600000000000
    assert df.iloc[0]["close"] == 102.0

    assert cache.get_last_updated("BTCUSDT", "1h") is not None
    assert cache.is_fresh("BTCUSDT", "1h", max_age_seconds=10)


def test_cache_in_progress_tick_update():
    cache = CandleStreamCache()
    c1 = {"timestamp": 1000, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1}
    c1_tick2 = {"timestamp": 1000, "open": 100, "high": 105, "low": 99, "close": 104, "volume": 2}

    cache.update("BTCUSDT", "1h", c1)
    cache.update("BTCUSDT", "1h", c1_tick2)

    df = cache.get("BTCUSDT", "1h")
    assert len(df) == 1
    assert df.iloc[0]["high"] == 105.0
    assert df.iloc[0]["close"] == 104.0
    assert df.iloc[0]["volume"] == 2.0


def test_cache_bounded_rolling_window():
    cache = CandleStreamCache(max_candles=3)
    for i in range(5):
        candle = {
            "timestamp": 1000 + i * 1000,
            "open": 10 + i,
            "high": 15 + i,
            "low": 5 + i,
            "close": 12 + i,
            "volume": 100,
        }
        cache.update("BTCUSDT", "1h", candle)

    df = cache.get("BTCUSDT", "1h")
    assert len(df) == 3
    # Should contain timestamps 3000, 4000, 5000 (0 and 1 dropped)
    assert list(df["timestamp"]) == [3000, 4000, 5000]


def test_cache_key_isolation():
    cache = CandleStreamCache()
    c_btc = {"timestamp": 1000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10}
    c_eth = {"timestamp": 1000, "open": 200, "high": 201, "low": 199, "close": 200, "volume": 20}

    cache.update("BTCUSDT", "1h", c_btc)
    cache.update("ETHUSDT", "1h", c_eth)
    cache.update("BTCUSDT", "15m", c_btc)

    df_btc_1h = cache.get("BTCUSDT", "1h")
    df_eth_1h = cache.get("ETHUSDT", "1h")
    df_btc_15m = cache.get("BTCUSDT", "15m")
    df_sol_1h = cache.get("SOLUSDT", "1h")

    assert df_btc_1h is not None and len(df_btc_1h) == 1
    assert df_eth_1h is not None and df_eth_1h.iloc[0]["close"] == 200.0
    assert df_btc_15m is not None and len(df_btc_15m) == 1
    assert df_sol_1h is None


def test_cache_limit_retrieval():
    cache = CandleStreamCache(max_candles=10)
    for i in range(10):
        candle = {
            "timestamp": 1000 + i * 10,
            "open": 1, "high": 2, "low": 0, "close": 1, "volume": 1
        }
        cache.update("BTCUSDT", "1h", candle)

    df = cache.get("BTCUSDT", "1h", limit=3)
    assert len(df) == 3
    assert list(df["timestamp"]) == [1070, 1080, 1090]


def test_cache_clear():
    cache = CandleStreamCache()
    c = {"timestamp": 1000, "open": 1, "high": 2, "low": 0, "close": 1, "volume": 1}
    cache.update("BTCUSDT", "1h", c)
    cache.update("ETHUSDT", "1h", c)

    cache.clear("BTCUSDT", "1h")
    assert cache.get("BTCUSDT", "1h") is None
    assert cache.get("ETHUSDT", "1h") is not None

    cache.clear()
    assert cache.get("ETHUSDT", "1h") is None


def test_cache_invalid_candle_structure():
    cache = CandleStreamCache()
    with pytest.raises(ValueError):
        cache.update("BTCUSDT", "1h", {"timestamp": 1000, "open": 10})


def test_cache_concurrent_access():
    cache = CandleStreamCache(max_candles=100)
    errors = []

    def writer(thread_id: int):
        try:
            for i in range(200):
                candle = {
                    "timestamp": 1000 + (i % 50) * 100,  # simulate combination of new & update ticks
                    "open": thread_id,
                    "high": thread_id + 1,
                    "low": thread_id - 1,
                    "close": thread_id,
                    "volume": i,
                }
                cache.update("BTCUSDT", "1h", candle)
                time.sleep(0.0001)
        except Exception as e:
            errors.append(e)

    def reader():
        try:
            for _ in range(200):
                df = cache.get("BTCUSDT", "1h")
                if df is not None:
                    _ = len(df)
                    _ = cache.is_fresh("BTCUSDT", "1h", max_age_seconds=5)
                time.sleep(0.0001)
        except Exception as e:
            errors.append(e)

    threads = []
    for t in range(3):
        threads.append(threading.Thread(target=writer, args=(t,)))
        threads.append(threading.Thread(target=reader))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert not errors, f"Concurrent execution generated errors: {errors}"
    df = cache.get("BTCUSDT", "1h")
    assert df is not None
    assert len(df) <= 100
