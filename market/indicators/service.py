"""Single source of computed indicators — calculated once, cached, reused."""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from market.cache import CacheManager
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine
from market_data.volume import VolumeEngine

logger = logging.getLogger(__name__)


class IndicatorService:
    """Compute and cache technical indicators.

    All consumers share the same cached indicator values —
    no duplicate computation across the platform.
    """

    def __init__(
        self,
        cache: Optional[CacheManager] = None,
        indicator_engine: Optional[IndicatorEngine] = None,
        volatility_engine: Optional[VolatilityEngine] = None,
        volume_engine: Optional[VolumeEngine] = None,
        cache_ttl: float = 300,
    ) -> None:
        self.cache = cache or CacheManager(default_ttl=cache_ttl)
        self._indicators = indicator_engine or IndicatorEngine()
        self._volatility = volatility_engine or VolatilityEngine()
        self._volume = volume_engine or VolumeEngine()
        self._cache_ttl = cache_ttl

    def get_indicators(
        self,
        symbol: str,
        timeframe: str,
        df: Optional[pd.DataFrame] = None,
    ) -> dict[str, Any]:
        """Return cached indicators, or compute and cache them."""
        cache_key = self.cache.make_key("indicators", symbol, timeframe)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if df is None or df.empty:
            logger.warning("No data to compute indicators for %s %s", symbol, timeframe)
            return {}

        indicators = self._indicators.calculate(df)
        vol = self._volatility.score(indicators)
        volume = self._volume.score(df)
        indicators["volatility"] = vol.get("volatility", 0)
        indicators["volatility_score"] = vol.get("score", 0)
        indicators["volume_score"] = volume.get("score", 0)

        self.cache.set(cache_key, indicators, ttl=self._cache_ttl)
        return indicators

    def get_indicator_values(
        self,
        symbol: str,
        timeframe: str,
        df: Optional[pd.DataFrame] = None,
    ) -> dict[str, float]:
        """Return only numeric indicator values for the given symbol/timeframe."""
        raw = self.get_indicators(symbol, timeframe, df)
        return {k: v for k, v in raw.items() if isinstance(v, (int, float))}

    def invalidate(self, symbol: str, timeframe: str) -> None:
        self.cache.invalidate(self.cache.make_key("indicators", symbol, timeframe))
