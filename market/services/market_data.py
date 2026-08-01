"""MarketDataService — single entry point for ALL market data.

No module should import HyperliquidCollector directly.
All market data flows through this service.

Responsibilities:
  - OHLCV
  - Ticker
  - Funding
  - Open Interest
  - Indicators (cached, computed once)
  - Features (categorical AI features)
  - Context (BTC, sessions, funding state)
  - Intelligence (funding, OI, Fear & Greed, News, Whale, Exchange Flow, Liquidity)
  - Asset model (unified representation)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd

from market.cache import CacheManager
from market.context import ContextService
from market.features import FeatureStore
from market.indicators import IndicatorService
from market.intelligence.service import IntelligenceService
from market.models import Asset, AssetMetadata, OHLCVData
from market.provider import HyperliquidProvider

logger = logging.getLogger(__name__)


class MarketDataService:
    """Single entry point for all market data in the Elite Platform."""

    def __init__(
        self,
        provider: Optional[HyperliquidProvider] = None,
        cache: Optional[CacheManager] = None,
        indicators: Optional[IndicatorService] = None,
        features: Optional[FeatureStore] = None,
        context: Optional[ContextService] = None,
        intelligence: Optional[IntelligenceService] = None,
    ) -> None:
        self.provider = provider or HyperliquidProvider()
        self.cache = cache or CacheManager()
        self.indicators = indicators or IndicatorService(cache=self.cache)
        self.features = features or FeatureStore()
        self.context = context or ContextService(provider=self.provider, cache=self.cache)
        self.intelligence = intelligence or IntelligenceService()

    # ── Raw market data ──────────────────────────────────────────────

    def get_ohlcv(
        self,
        symbol: str = "BTC",
        timeframe: str = "1h",
        limit: int = 500,
    ) -> pd.DataFrame:
        cache_key = self.cache.make_key("ohlcv", symbol, timeframe, str(limit))
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        df = self.provider.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        if not df.empty:
            self.cache.set(cache_key, df, ttl=30)
        return df

    def get_ticker(self, symbol: str) -> dict[str, Any]:
        return self.provider.get_ticker(symbol)

    def get_funding(self, symbol: str) -> dict[str, Any]:
        return self.provider.get_funding(symbol)

    def get_open_interest(self, symbol: str) -> dict[str, Any]:
        return self.provider.get_open_interest(symbol)

    # ── Asset ────────────────────────────────────────────────────────

    def get_asset(self, symbol: str, timeframe: str = "1h") -> Asset:
        """Return a fully enriched Asset for the given symbol."""
        cache_key = self.cache.make_key("asset", symbol, timeframe)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        ohlcv = self.get_ohlcv(symbol=symbol, timeframe=timeframe)

        if ohlcv.empty:
            asset = Asset(
                symbol=symbol,
                metadata=AssetMetadata(symbol=symbol),
            )
            self.cache.set(cache_key, asset, ttl=10)
            return asset

        price = float(ohlcv["close"].iloc[-1])
        indicators = self.indicators.get_indicators(symbol, timeframe, ohlcv)
        features = self.features.extract(indicators)
        ctx = self.context.get_context()

        asset = Asset(
            symbol=symbol,
            metadata=AssetMetadata(symbol=symbol),
            price=price,
            ohlcv=ohlcv,
            indicators=indicators,
            features=features,
            context=ctx,
            timestamp=datetime.now(timezone.utc),
        )

        asset = self.intelligence.enrich(asset)

        self.cache.set(cache_key, asset, ttl=15)
        return asset

    def get_intelligence(self, symbol: str, timeframe: str = "1h") -> dict[str, Any]:
        """Return intelligence bundle for the given symbol."""
        asset = self.get_asset(symbol, timeframe)
        bundle = asset.intelligence
        if bundle is None:
            return {}
        return {
            "funding": bundle.funding,
            "open_interest": bundle.open_interest,
            "btc_context": bundle.btc_context,
            "fear_greed": bundle.fear_greed,
            "news": bundle.news,
            "whales": bundle.whales,
            "market_session": bundle.market_session,
            "exchange_flow": bundle.exchange_flow,
            "liquidity_context": bundle.liquidity_context,
            "confidence": bundle.confidence,
            "feature_count": bundle.feature_count,
            "available_features": bundle.available_features,
        }

    def get_assets(
        self,
        symbols: list[str],
        timeframe: str = "1h",
    ) -> dict[str, Asset]:
        return {s: self.get_asset(s, timeframe) for s in symbols}

    # ── Convenience ──────────────────────────────────────────────────

    def get_price(self, symbol: str) -> float:
        asset = self.get_asset(symbol)
        return asset.price

    def get_indicators(self, symbol: str, timeframe: str = "1h") -> dict[str, Any]:
        ohlcv = self.get_ohlcv(symbol=symbol, timeframe=timeframe)
        return self.indicators.get_indicators(symbol, timeframe, ohlcv)

    def get_features(self, symbol: str, timeframe: str = "1h", side: str = "LONG") -> dict[str, Any]:
        indicators = self.get_indicators(symbol, timeframe)
        return self.features.extract(indicators, side)

    def get_context(self) -> dict[str, Any]:
        return self.context.get_context()

    # ── Cache management ─────────────────────────────────────────────

    def invalidate_asset(self, symbol: str, timeframe: str = "1h") -> None:
        self.cache.invalidate(self.cache.make_key("asset", symbol, timeframe))
        self.cache.invalidate(self.cache.make_key("indicators", symbol, timeframe))

    def invalidate_all(self) -> None:
        self.cache.clear()
