"""Live market data engine providing price streams, candle updates, and snapshots."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine


logger = logging.getLogger(__name__)

_CACHE_TTL = 60.0


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
        collector: Optional[HyperliquidCollector] = None,
        indicators: Optional[IndicatorEngine] = None,
        cache_ttl: float = _CACHE_TTL,
    ) -> None:
        self.collector = collector or HyperliquidCollector()
        self.indicators = indicators or IndicatorEngine()
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, MarketSnapshot]] = {}

    def _cache_key(self, symbol: str, timeframe: str, limit: int) -> str:
        return f"{symbol}:{timeframe}:{limit}"

    def _get_cached(self, key: str) -> Optional[MarketSnapshot]:
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
                timestamp=datetime.now(timezone.utc).isoformat(),
                candles=[],
            )
            self._cache[key] = (time.monotonic(), result)
            return result

        latest = df.iloc[-1]
        price = float(latest["close"])
        volume = float(df["volume"].tail(24).sum()) if len(df) >= 24 else float(df["volume"].sum())
        high_24h = float(df["high"].tail(24).max()) if len(df) >= 24 else float(df["high"].max())
        low_24h = float(df["low"].tail(24).min()) if len(df) >= 24 else float(df["low"].min())
        change_24h = ((price - float(df.iloc[-24]["close"])) / float(df.iloc[-24]["close"]) * 100) if len(df) >= 24 else 0.0

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
            timestamp=datetime.now(timezone.utc).isoformat(),
            candles=candles[-50:],
        )
        self._cache[key] = (time.monotonic(), result)
        return result
