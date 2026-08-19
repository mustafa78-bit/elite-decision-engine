"""Unit tests for CandleStreamCache."""

import threading
import time
from unittest.mock import patch

import pandas as pd
import pytest

from market.stream.cache import CandleStreamCache, normalize_symbol, normalize_timeframe


def test_normalize_symbol_and_timeframe():
    assert normalize_symbol("btc/usdt") == "BTC"
    assert normalize_symbol("eth-usdt") == "ETH"
    assert normalize_symbol(" SOL/USDT ") == "SOL"
    assert normalize_symbol("BTCUSDT") == "BTC"
    assert normalize_symbol("ETHUSD") == "ETH"

    assert normalize_timeframe("1H") == "1h"
    assert normalize_timeframe(" 15M ") == "15m"


def test_candle_stream_cache_update_and_get_ohlcv():
    cache = CandleStreamCache(max_len=5)

    assert not cache.has_symbol("BTC", "1h")
    df_empty = cache.get_ohlcv("BTC", "1h")
    assert isinstance(df_empty, pd.DataFrame)
    assert list(df_empty.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert len(df_empty) == 0

    # Initial update
    cache.update_candle("BTCUSDT", "1h", 1000, 100.0, 105.0, 99.0, 104.0, 10.0)
    assert cache.has_symbol("BTC", "1h")
    assert cache.has_symbol("BTCUSDT", "1h")

    latest = cache.get_latest_candle("BTC", "1h")
    assert latest is not None
    assert latest["timestamp"] == 1000
    assert latest["close"] == 104.0

    # In-place update (same timestamp)
    cache.update_candle("BTC/USDT", "1h", 1000, 100.0, 107.0, 99.0, 106.0, 15.0)
    latest2 = cache.get_latest_candle("BTC", "1h")
    assert latest2["high"] == 107.0
    assert latest2["close"] == 106.0
    assert latest2["volume"] == 15.0

    # Append newer candle
    cache.update_candle("BTC", "1h", 2000, 106.0, 110.0, 105.0, 109.0, 20.0)
    df = cache.get_ohlcv("BTCUSDT", "1h")
    assert len(df) == 2
    assert list(df["timestamp"]) == [1000, 2000]
    assert list(df["close"]) == [106.0, 109.0]
    assert df["open"].dtype == float


def test_candle_stream_cache_limit_and_out_of_order():
    cache = CandleStreamCache(max_len=3)

    for i in range(1, 6):
        cache.update_candle("ETH", "15m", i * 1000, i * 10, i * 10 + 5, i * 10 - 2, i * 10 + 2, i * 100)

    df = cache.get_ohlcv("ETH", "15m")
    assert len(df) == 3
    assert list(df["timestamp"]) == [3000, 4000, 5000]

    # Test limit argument
    df_slice = cache.get_ohlcv("ETH", "15m", limit=2)
    assert len(df_slice) == 2
    assert list(df_slice["timestamp"]) == [4000, 5000]

    # Test out-of-order update for timestamp 4000
    cache.update_candle("ETH", "15m", 4000, 40, 49, 38, 48, 999)
    latest = cache.get_latest_candle("ETH", "15m")
    assert latest["timestamp"] == 5000  # latest should still be 5000

    df_updated = cache.get_ohlcv("ETH", "15m")
    row_4000 = df_updated[df_updated["timestamp"] == 4000].iloc[0]
    assert row_4000["high"] == 49.0
    assert row_4000["volume"] == 999.0


def test_candle_stream_cache_freshness_and_clear():
    cache = CandleStreamCache()

    assert not cache.is_fresh("SOL", "1h")

    with patch("time.monotonic", return_value=100.0):
        cache.update_candle("SOL", "1h", 1000, 20.0, 21.0, 19.5, 20.5, 50.0)

    with patch("time.monotonic", return_value=200.0):
        assert cache.is_fresh("SOL", "1h", max_age_seconds=150.0)
        assert not cache.is_fresh("SOL", "1h", max_age_seconds=50.0)

    assert cache.get_symbols_and_timeframes() == [("SOL", "1h")]

    # Clear specific key
    cache.clear("SOL", "1h")
    assert not cache.has_symbol("SOL", "1h")
    assert not cache.is_fresh("SOL", "1h")
    assert cache.get_symbols_and_timeframes() == []

    # Clear all
    cache.update_candle("AVAX", "4h", 1000, 30.0, 31.0, 29.0, 30.5, 10.0)
    assert cache.has_symbol("AVAX", "4h")
    cache.clear()
    assert not cache.has_symbol("AVAX", "4h")


def test_candle_stream_cache_thread_safety():
    cache = CandleStreamCache(max_len=100)
    errors = []

    def writer(sym_id):
        try:
            for i in range(100):
                cache.update_candle(f"COIN{sym_id}", "1h", i * 10, i * 1.0, i * 1.1, i * 0.9, i * 1.05, 100.0)
                time.sleep(0.0001)
        except Exception as e:
            errors.append(e)

    def reader(sym_id):
        try:
            for _ in range(100):
                cache.get_ohlcv(f"COIN{sym_id}", "1h")
                cache.get_latest_candle(f"COIN{sym_id}", "1h")
                cache.is_fresh(f"COIN{sym_id}", "1h")
                time.sleep(0.0001)
        except Exception as e:
            errors.append(e)

    threads = []
    for s in range(5):
        t1 = threading.Thread(target=writer, args=(s,))
        t2 = threading.Thread(target=reader, args=(s,))
        threads.extend([t1, t2])
        t1.start()
        t2.start()

    for t in threads:
        t.join()

    assert not errors
    assert len(cache.get_symbols_and_timeframes()) == 5
