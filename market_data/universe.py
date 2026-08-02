"""Dynamic coin universe (top N by Binance 24h volume) provider."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from config import COIN_UNIVERSE_SIZE

logger = logging.getLogger(__name__)

_DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
CACHE_INTERVAL_SECONDS = 3600  # 1 hour
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"


class BinanceUniverseProvider:
    """Provides a dynamic coin universe of top USDT-quoted symbols by 24h volume on Binance."""

    def __init__(
        self,
        cache_interval: int = CACHE_INTERVAL_SECONDS,
        url: str = BINANCE_TICKER_URL,
    ) -> None:
        self.cache_interval = cache_interval
        self.url = url
        self._cached_symbols: list[str] | None = None
        self._last_updated: float = 0.0

    def get_top_volume_symbols(self, n: int | None = None) -> list[str]:
        """Fetch and return top N Binance USDT symbols sorted by 24h quote volume.

        If fetching fails, fall back to the cached list, or to _DEFAULT_SYMBOLS if cache is empty.
        """
        target_n = n if n is not None else COIN_UNIVERSE_SIZE
        now = time.time()

        # If cache is valid, return it
        if self._cached_symbols is not None and (now - self._last_updated) < self.cache_interval:
            return self._cached_symbols[:target_n]

        try:
            logger.info("Fetching 24h ticker data from Binance to refresh coin universe...")
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise ValueError(f"Expected list response from Binance, got {type(data).__name__}")

            # Filter, parse, and sort
            usdt_pairs = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                symbol = item.get("symbol")
                if symbol and isinstance(symbol, str) and symbol.endswith("USDT"):
                    # Check quoteVolume
                    quote_vol_str = item.get("quoteVolume")
                    if quote_vol_str is not None:
                        try:
                            quote_vol = float(quote_vol_str)
                            usdt_pairs.append((symbol, quote_vol))
                        except (ValueError, TypeError):
                            continue

            # Sort descending by quote volume
            usdt_pairs.sort(key=lambda x: x[1], reverse=True)
            sorted_symbols = [pair[0] for pair in usdt_pairs]

            if sorted_symbols:
                self._cached_symbols = sorted_symbols
                self._last_updated = now
                logger.info(
                    "Successfully updated coin universe cache. Found %d USDT pairs.",
                    len(sorted_symbols),
                )
                return sorted_symbols[:target_n]
            else:
                raise ValueError("No USDT-quoted symbols with valid quoteVolume found in response")

        except Exception as e:
            logger.warning(
                "Failed to refresh dynamic coin universe from Binance: %s. Falling back to cached data or defaults.",
                e,
            )
            # Safe fallback: previously cached data
            if self._cached_symbols is not None:
                return self._cached_symbols[:target_n]
            # Hardcoded defaults
            return _DEFAULT_SYMBOLS[:target_n]


# Singleton instance for platform-wide usage
_provider = BinanceUniverseProvider()


def get_top_volume_symbols(n: int | None = None) -> list[str]:
    """Helper function to get top volume symbols using the global provider singleton."""
    return _provider.get_top_volume_symbols(n)
