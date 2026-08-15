"""Live market data engine providing price streams, candle updates, and snapshots."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any, Optional

from market.provider import MultiProvider
from market.provider.base import DataProvider
from market_data.indicators import IndicatorEngine

logger = logging.getLogger(__name__)

_CACHE_TTL = 60.0

_TIMEFRAME_MINUTES = {
    "1m": 1, "5m": 5, "15m": 15, "30m": 30,
    "1h": 60, "4h": 240, "1d": 1440, "1w": 10080,
}


def _candles_per_24h(timeframe: str) -> int:
    """Number of candles that span a real 24h window for this timeframe."""
    minutes = _TIMEFRAME_MINUTES.get(timeframe, 60)
    return max(1, 1440 // minutes)


@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: str
    candles: list[Candle] = field(default_factory=list)


class LiveMarketEngine:
    """Fetches and caches live market data snapshots."""

    def __init__(
        self,
        collector: DataProvider | None = None,
        indicators: IndicatorEngine | None = None,
        cache_ttl: float = _CACHE_TTL,
    ) -> None:
        self.collector = collector or MultiProvider()
        self.indicators = indicators or IndicatorEngine()
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, MarketSnapshot]] = {}

    def _cache_key(self, symbol: str, timeframe: str, limit: int) -> str:
        return f"{symbol}:{timeframe}:{limit}"

    def _get_cached(self, key: str) -> MarketSnapshot | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, snapshot = entry
        if time.monotonic() - ts < self.cache_ttl:
            return snapshot
        logger.debug("Cache expired for %s (age=%.1fs)", key, time.monotonic() - ts)
        del self._cache[key]
        return None

    def snapshot(self, symbol: str = "BTC", timeframe: str = "1h", limit: int = 100) -> MarketSnapshot:
        key = self._cache_key(symbol, timeframe, limit)
        cached = self._get_cached(key)
        if cached is not None:
            logger.debug("Cache hit for %s", key)
            return cached
        logger.debug("Cache miss for %s — fetching", key)
        df = self.collector.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

        if df.empty:
            logger.warning("Empty market data for %s %s", symbol, timeframe)
            result = MarketSnapshot(
                symbol=symbol,
                price=0.0,
                volume_24h=0.0,
                change_24h=0.0,
                high_24h=0.0,
                low_24h=0.0,
                timestamp=datetime.now(UTC).isoformat(),
                candles=[],
            )
            self._cache[key] = (time.monotonic(), result)
            return result

        latest = df.iloc[-1]
        price = float(latest["close"])
        window = _candles_per_24h(timeframe)
        volume = float(df["volume"].tail(window).sum()) if len(df) >= window else float(df["volume"].sum())
        high_24h = float(df["high"].tail(window).max()) if len(df) >= window else float(df["high"].max())
        low_24h = float(df["low"].tail(window).min()) if len(df) >= window else float(df["low"].min())
        if len(df) >= window:
            price_24h_ago = float(df.iloc[-window]["close"])
            change_24h = ((price - price_24h_ago) / price_24h_ago * 100) if price_24h_ago > 0 else 0.0
        else:
            change_24h = 0.0

        candles = [
            Candle(
                timestamp=int(row["timestamp"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for _, row in df.iterrows()
        ]

        result = MarketSnapshot(
            symbol=symbol,
            price=round(price, 2),
            volume_24h=round(volume, 2),
            change_24h=round(change_24h, 2),
            high_24h=round(high_24h, 2),
            low_24h=round(low_24h, 2),
            timestamp=datetime.now(UTC).isoformat(),
            candles=candles[-50:],
        )
        self._cache[key] = (time.monotonic(), result)
        return result
