"""Thread-safe in-memory rolling candle cache for WebSocket market data streams."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

_DEFAULT_MAX_LEN = 500

_shared_cache_instance: CandleStreamCache | None = None
_shared_cache_lock = threading.Lock()


def normalize_symbol(symbol: str) -> str:
    """Normalize symbol representation to standard base symbol (e.g., 'btc/usdt' or 'BTC-USDT' -> 'BTC')."""
    clean = symbol.upper().replace("/", "").replace("-", "").strip()
    for suffix in ("USDT", "USDC", "BUSD", "USD", "PERP"):
        if clean.endswith(suffix) and len(clean) > len(suffix):
            return clean[: -len(suffix)]
    return clean


def normalize_timeframe(tf: str) -> str:
    """Normalize timeframe string (e.g., '1H' -> '1h')."""
    return tf.lower().strip()


class CandleStreamCache:
    """Thread-safe rolling candle store indexed by (symbol, timeframe)."""

    def __init__(self, max_len: int = _DEFAULT_MAX_LEN) -> None:
        self._max_len = max_len
        self._cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self._updated_at: dict[tuple[str, str], float] = {}
        self._lock = threading.RLock()

    def _make_key(self, symbol: str, timeframe: str) -> tuple[str, str]:
        return (normalize_symbol(symbol), normalize_timeframe(timeframe))

    def update_candle(
        self,
        symbol: str,
        timeframe: str,
        timestamp: int,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        is_closed: bool = False,
    ) -> None:
        """Push a candle update into the rolling cache.

        If a candle with the exact same timestamp exists as the latest entry,
        it updates that candle in place. If it's newer, it appends it.
        If it's older, it places/updates it at the correct sorted position.
        """
        key = self._make_key(symbol, timeframe)
        candle = {
            "timestamp": int(timestamp),
            "open": float(open_),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": float(volume),
        }

        with self._lock:
            self._updated_at[key] = time.monotonic()
            if key not in self._cache:
                self._cache[key] = [candle]
                return

            candles = self._cache[key]
            if not candles:
                candles.append(candle)
                return

            latest_ts = candles[-1]["timestamp"]
            if timestamp == latest_ts:
                candles[-1] = candle
            elif timestamp > latest_ts:
                candles.append(candle)
                if len(candles) > self._max_len:
                    candles.pop(0)
            else:
                # Out-of-order update
                for i, existing in enumerate(candles):
                    if existing["timestamp"] == timestamp:
                        candles[i] = candle
                        return
                    if existing["timestamp"] > timestamp:
                        candles.insert(i, candle)
                        if len(candles) > self._max_len:
                            candles.pop(0)
                        return
                candles.append(candle)

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> pd.DataFrame:
        """Return a DataFrame with up to `limit` candles matching DataProvider format."""
        key = self._make_key(symbol, timeframe)
        required_cols = ["timestamp", "open", "high", "low", "close", "volume"]

        with self._lock:
            candles = self._cache.get(key)
            if not candles:
                return pd.DataFrame(columns=required_cols)

            slice_candles = list(candles[-limit:]) if limit > 0 else list(candles)

        df = pd.DataFrame(slice_candles)
        if df.empty:
            return pd.DataFrame(columns=required_cols)

        # Ensure all columns exist and have correct dtypes
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = df[col].astype(float)
            else:
                df[col] = 0.0

        if "timestamp" in df.columns:
            df["timestamp"] = df["timestamp"].astype(int)

        return df[required_cols].reset_index(drop=True)

    def get_latest_candle(self, symbol: str, timeframe: str) -> dict[str, Any] | None:
        """Return a copy of the most recent candle for the given symbol and timeframe."""
        key = self._make_key(symbol, timeframe)
        with self._lock:
            candles = self._cache.get(key)
            if not candles:
                return None
            return dict(candles[-1])

    def is_fresh(
        self,
        symbol: str,
        timeframe: str,
        max_age_seconds: float = 300.0,
    ) -> bool:
        """Check if stream updates have been received within `max_age_seconds`."""
        key = self._make_key(symbol, timeframe)
        with self._lock:
            last_time = self._updated_at.get(key)
            if last_time is None:
                return False
            return (time.monotonic() - last_time) <= max_age_seconds

    def has_symbol(self, symbol: str, timeframe: str) -> bool:
        """Check if any candles are cached for symbol and timeframe."""
        key = self._make_key(symbol, timeframe)
        with self._lock:
            candles = self._cache.get(key)
            return bool(candles)

    def get_symbols_and_timeframes(self) -> list[tuple[str, str]]:
        """Return list of active (symbol, timeframe) tuples in the cache."""
        with self._lock:
            return [k for k, v in self._cache.items() if v]

    def clear(self, symbol: str | None = None, timeframe: str | None = None) -> None:
        """Clear cache entries."""
        with self._lock:
            if symbol is not None and timeframe is not None:
                key = self._make_key(symbol, timeframe)
                self._cache.pop(key, None)
                self._updated_at.pop(key, None)
            else:
                self._cache.clear()
                self._updated_at.clear()


def get_shared_candle_stream_cache() -> CandleStreamCache:
    """Process-wide singleton -- same lazy double-checked-locking pattern as
    market/provider/multi.py::get_shared_multi_provider(). This is the one
    real cache instance Step 2's WebSocket clients write into and the
    instance Step 3's real read path will read from -- there must be
    exactly one shared instance the whole running app agrees on, not one
    per caller.
    """
    global _shared_cache_instance
    if _shared_cache_instance is None:
        with _shared_cache_lock:
            if _shared_cache_instance is None:
                _shared_cache_instance = CandleStreamCache()
    return _shared_cache_instance
