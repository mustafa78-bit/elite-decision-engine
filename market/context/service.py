"""Global market context — BTC, dominance, sessions, funding state."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from market.cache import CacheManager
from market.provider import HyperliquidProvider
from market_data.collector import HyperliquidCollector

logger = logging.getLogger(__name__)


class ContextService:
    """Provides broader market context independent of any single asset."""

    def __init__(
        self,
        provider: Optional[HyperliquidProvider] = None,
        cache: Optional[CacheManager] = None,
        cache_ttl: float = 300,
    ) -> None:
        self.provider = provider or HyperliquidProvider()
        self.cache = cache or CacheManager(default_ttl=cache_ttl)
        self._cache_ttl = cache_ttl

    def get_btc_context(self) -> dict[str, Any]:
        """BTC-centric market context."""
        cache_key = self.cache.make_key("context", "btc")
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        df = self.provider.get_ohlcv(symbol="BTC", timeframe="1h", limit=100)
        if df.empty:
            return {"btc_price": 0.0, "btc_trend": "UNKNOWN", "available": False}

        price = float(df["close"].iloc[-1])
        ema20 = float(df["close"].rolling(20).mean().iloc[-1]) if len(df) >= 20 else price
        ema50 = float(df["close"].rolling(50).mean().iloc[-1]) if len(df) >= 50 else price

        if ema20 > ema50:
            trend = "BULLISH"
        elif ema20 < ema50:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        ctx = {
            "btc_price": price,
            "btc_trend": trend,
            "btc_ema20": round(ema20, 2),
            "btc_ema50": round(ema50, 2),
            "available": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.cache.set(cache_key, ctx, ttl=self._cache_ttl)
        return ctx

    def get_market_session(self) -> str:
        """Return current market session: ASIAN, LONDON, NY, or CLOSED."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        if 0 <= hour < 8:
            return "ASIAN"
        if 8 <= hour < 13:
            return "LONDON"
        if 13 <= hour < 22:
            return "NY"
        return "CLOSED"

    def get_funding_state(self, symbol: str = "BTC") -> dict[str, Any]:
        """Current funding rate state for the given symbol."""
        funding = self.provider.get_funding(symbol)
        rate = funding.get("rate", 0.0)
        if rate > 0.01:
            state = "HIGH_LONG"
        elif rate > 0.001:
            state = "MODERATE_LONG"
        elif rate < -0.01:
            state = "HIGH_SHORT"
        elif rate < -0.001:
            state = "MODERATE_SHORT"
        else:
            state = "NEUTRAL"
        return {"symbol": symbol, "funding_rate": rate, "state": state}

    def get_context(self) -> dict[str, Any]:
        """Return full market context bundle."""
        btc = self.get_btc_context()
        session = self.get_market_session()
        funding = self.get_funding_state("BTC")
        return {
            "btc": btc,
            "session": session,
            "funding": funding,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
