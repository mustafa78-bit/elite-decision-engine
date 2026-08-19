"""Thread-safe rolling in-memory cache for market candle streams."""

import time
import threading
from typing import Optional, Dict, List, Any
import pandas as pd


class CandleStreamCache:
    """
    In-memory rolling candle cache indexed by (symbol, timeframe).

    Stores up to `max_candles` per key (default 500).
    Thread-safe: wrapped in a threading.Lock to support concurrent
    asyncio writes and synchronous reader threads.
    """

    def __init__(self, max_candles: int = 500):
        self.max_candles = max_candles
        self._lock = threading.Lock()
        # Storage schema: key (symbol, timeframe) -> list of candle dicts
        # Candle dict standard keys: timestamp, open, high, low, close, volume
        self._cache: Dict[tuple[str, str], List[Dict[str, Any]]] = {}
        # Storage schema: key (symbol, timeframe) -> last update epoch seconds (float)
        self._last_updated: Dict[tuple[str, str], float] = {}

    def update(self, symbol: str, timeframe: str, candle: Dict[str, Any]) -> None:
        """
        Update or append a candle for a given (symbol, timeframe) key.

        If the incoming candle's timestamp matches the latest cached candle,
        it updates that candle in-place (handling real-time tick updates for in-progress candles).
        Otherwise, it appends the new candle and drops oldest candles if length exceeds max_candles.
        """
        key = (symbol, timeframe)
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(candle.keys()):
            raise ValueError(f"Candle dict missing required keys: {required_cols - set(candle.keys())}")

        formatted_candle = {
            "timestamp": int(candle["timestamp"]),
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"]),
            "volume": float(candle["volume"]),
        }

        with self._lock:
            if key not in self._cache:
                self._cache[key] = []

            candles = self._cache[key]
            if candles and candles[-1]["timestamp"] == formatted_candle["timestamp"]:
                # Update existing in-progress candle
                candles[-1] = formatted_candle
            else:
                # Append new candle
                candles.append(formatted_candle)
                if len(candles) > self.max_candles:
                    self._cache[key] = candles[-self.max_candles:]

            self._last_updated[key] = time.time()

    def get(self, symbol: str, timeframe: str, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Retrieve cached candles for (symbol, timeframe) as a pandas DataFrame.

        Returns None if no data is cached for the key.
        DataFrame columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
        """
        key = (symbol, timeframe)
        with self._lock:
            if key not in self._cache or not self._cache[key]:
                return None

            candles = list(self._cache[key])

        if limit is not None and limit > 0:
            candles = candles[-limit:]

        df = pd.DataFrame(candles)
        cols = ["timestamp", "open", "high", "low", "close", "volume"]
        return df[cols].reset_index(drop=True)

    def get_last_updated(self, symbol: str, timeframe: str) -> Optional[float]:
        """Return the epoch timestamp when the cache key was last updated, or None if empty."""
        key = (symbol, timeframe)
        with self._lock:
            return self._last_updated.get(key)

    def is_fresh(self, symbol: str, timeframe: str, max_age_seconds: float) -> bool:
        """Return True if cached data exists for key and was updated within max_age_seconds."""
        last_updated = self.get_last_updated(symbol, timeframe)
        if last_updated is None:
            return False
        return (time.time() - last_updated) <= max_age_seconds

    def clear(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> None:
        """Clear cache for a specific key or all keys if none provided."""
        with self._lock:
            if symbol and timeframe:
                key = (symbol, timeframe)
                self._cache.pop(key, None)
                self._last_updated.pop(key, None)
            else:
                self._cache.clear()
                self._last_updated.clear()
