"""Routes each symbol to the Hyperliquid, Binance, or Bybit provider per
config.SYMBOL_PROVIDER_ASSIGNMENT, with a shared per-provider rate limiter.

Step 2 of 3 in the Hyperliquid-rate-limit fix (see
SPRINT_JULES_HYPERLIQUID_NO_GLOBAL_RATE_LIMIT.md / SPRINT_JULES_BINANCE_PROVIDER_STEP2.md
for the full background). Bybit added 2026-08-19 as a third provider after
Hyperliquid kept showing real, recurring 429s even split two ways -- see
market/provider/bybit.py's module docstring.

Request coalescing (deduping identical concurrent (provider, symbol, timeframe)
OHLCV requests within a short window) is deliberately NOT implemented here --
left for a later step once real call-site migration shows the actual
concurrency pattern; adding it now would be premature.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

import pandas as pd

from config import SYMBOL_PROVIDER_ASSIGNMENT
from market.provider.base import DataProvider
from market.provider.binance import BinanceProvider
from market.provider.bybit import BybitProvider
from market.provider.hyperliquid import HyperliquidProvider
from market.provider.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)

# Lowered from 5.0 -- real 429 observations 2026-08-21 (236 in a short
# window) showed 5/sec was still too aggressive for Hyperliquid's actual
# tolerance once several subsystems (scanner, chart overlays, screenshot
# capture) poll concurrently. Paired with market_data/collector.py no longer
# blindly retrying on 429 (see that module) -- retries were compounding the
# problem by adding load on top of what already triggered the rate limit.
DEFAULT_REQUESTS_PER_SECOND = 3.0


class MultiProvider:
    """Implements DataProvider by delegating each call to whichever real
    provider (Hyperliquid, Binance, or Bybit) config.SYMBOL_PROVIDER_ASSIGNMENT
    assigns the given symbol to, rate-limited per provider.
    """

    def __init__(
        self,
        hyperliquid_provider: DataProvider | None = None,
        binance_provider: DataProvider | None = None,
        bybit_provider: DataProvider | None = None,
        requests_per_second: float = DEFAULT_REQUESTS_PER_SECOND,
    ) -> None:
        self._hyperliquid = hyperliquid_provider or HyperliquidProvider()
        self._binance = binance_provider or BinanceProvider()
        self._bybit = bybit_provider or BybitProvider()
        self._hyperliquid_limiter = TokenBucketRateLimiter(requests_per_second)
        self._binance_limiter = TokenBucketRateLimiter(requests_per_second)
        self._bybit_limiter = TokenBucketRateLimiter(requests_per_second)

    def _resolve(self, symbol: str) -> tuple[DataProvider, TokenBucketRateLimiter]:
        """Symbols not in the fixed 25-symbol universe (temp-watch additions,
        AssetDetail's free-text lookup) always resolve to Hyperliquid -- this
        table only has assignments for the planned, bounded universe.
        """
        assignment = SYMBOL_PROVIDER_ASSIGNMENT.get(symbol, "hyperliquid")
        if assignment == "binance":
            return self._binance, self._binance_limiter
        if assignment == "bybit":
            return self._bybit, self._bybit_limiter
        return self._hyperliquid, self._hyperliquid_limiter

    def get_ohlcv(
        self,
        symbol: str = "BTC",
        timeframe: str = "1h",
        limit: int = 500,
    ) -> pd.DataFrame:
        provider, limiter = self._resolve(symbol)
        limiter.acquire()
        return provider.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

    def get_ticker(self, symbol: str) -> dict[str, Any]:
        provider, limiter = self._resolve(symbol)
        limiter.acquire()
        return provider.get_ticker(symbol)

    def get_funding(self, symbol: str) -> dict[str, Any]:
        provider, limiter = self._resolve(symbol)
        limiter.acquire()
        return provider.get_funding(symbol)

    def get_open_interest(self, symbol: str) -> dict[str, Any]:
        provider, limiter = self._resolve(symbol)
        limiter.acquire()
        return provider.get_open_interest(symbol)

    def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        provider, limiter = self._resolve(symbol)
        limiter.acquire()
        return provider.get_orderbook(symbol, depth=depth)

    def get_trades(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        provider, limiter = self._resolve(symbol)
        limiter.acquire()
        return provider.get_trades(symbol, limit=limit)


_shared_instance: MultiProvider | None = None
_shared_instance_lock = threading.Lock()


def get_shared_multi_provider() -> MultiProvider:
    """Process-wide singleton -- every real call site used to default to its
    own `MultiProvider()`, so 19 independent instances each ran their own
    per-provider rate limiter with zero coordination between them (same
    "unshared throttle" bug this whole module was built to fix, just
    reintroduced one layer up). Live-observed 2026-08-19: 3 concurrent scan
    loops logging "Scanning 25 symbols on 1h" within the same second, each
    presumably burning its own 5 req/s allowance against the same upstream
    APIs. Callers should default to this instead of constructing their own.
    """
    global _shared_instance
    if _shared_instance is None:
        with _shared_instance_lock:
            if _shared_instance is None:
                _shared_instance = MultiProvider()
    return _shared_instance
