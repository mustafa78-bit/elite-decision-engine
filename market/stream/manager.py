"""Orchestrates all 3 provider WebSocket clients (Binance/Bybit/Hyperliquid)
against one shared CandleStreamCache, routed per symbol exactly the way
market/provider/multi.py::MultiProvider routes REST calls.

Real connection lifecycle -- api/main.py's lifespan() starts/stops this on
real app boot/shutdown (see that module). The cache these connections
populate is not read by any real caller yet; that's a later step. Running
real, populated-but-unread connections in production is intentional: a
safe soak period to verify the WS layer stays healthy under real load
before anything depends on it.
"""

from __future__ import annotations

import asyncio
import logging
import threading

from config import FIXED_COIN_UNIVERSE, SYMBOL_PROVIDER_ASSIGNMENT
from market.stream.binance_ws import BinanceWSClient
from market.stream.bybit_ws import BybitWSClient
from market.stream.cache import CandleStreamCache, get_shared_candle_stream_cache
from market.stream.hyperliquid_ws import HyperliquidWSClient

logger = logging.getLogger(__name__)

# The small, real set of timeframes this app actually requests --
# SCANNER_TIMEFRAME's default "15m", MTFEngine's "15m"/"1h"/"4h", and
# dashboards' "1h"/"4h"/"1d" -- not every timeframe each exchange supports.
DEFAULT_TIMEFRAMES: list[str] = ["15m", "1h", "4h", "1d"]

_shared_manager_instance: MarketStreamManager | None = None
_shared_manager_lock = threading.Lock()


class MarketStreamManager:
    """Builds and runs the 3 provider WS clients together, routing each
    symbol to whichever client matches its SYMBOL_PROVIDER_ASSIGNMENT
    entry -- symbols outside that table (temp-watch additions, free-text
    lookups) are out of scope for the WS layer entirely and stay
    REST-only, matching MultiProvider._resolve()'s existing fallback.
    """

    def __init__(
        self,
        cache: CandleStreamCache | None = None,
        symbols: list[str] | None = None,
        timeframes: list[str] | None = None,
        binance_client: BinanceWSClient | None = None,
        bybit_client: BybitWSClient | None = None,
        hyperliquid_client: HyperliquidWSClient | None = None,
    ) -> None:
        self.cache = cache or get_shared_candle_stream_cache()
        self.timeframes = list(timeframes or DEFAULT_TIMEFRAMES)
        target_symbols = symbols if symbols is not None else FIXED_COIN_UNIVERSE

        binance_symbols: list[str] = []
        bybit_symbols: list[str] = []
        hyperliquid_symbols: list[str] = []
        for symbol in target_symbols:
            assignment = SYMBOL_PROVIDER_ASSIGNMENT.get(symbol, "hyperliquid")
            if assignment == "binance":
                binance_symbols.append(symbol)
            elif assignment == "bybit":
                bybit_symbols.append(symbol)
            else:
                hyperliquid_symbols.append(symbol)

        self.binance = binance_client or BinanceWSClient(
            cache=self.cache, symbols=binance_symbols, timeframes=self.timeframes
        )
        self.bybit = bybit_client or BybitWSClient(
            cache=self.cache, symbols=bybit_symbols, timeframes=self.timeframes
        )
        self.hyperliquid = hyperliquid_client or HyperliquidWSClient(
            cache=self.cache, symbols=hyperliquid_symbols, timeframes=self.timeframes
        )
        self._clients = {
            "binance": self.binance,
            "bybit": self.bybit,
            "hyperliquid": self.hyperliquid,
        }

    async def start_all(self) -> None:
        """Start all 3 clients -- one client failing to start must not
        prevent the other two from running."""
        for name, client in self._clients.items():
            try:
                await client.start()
            except Exception as e:
                logger.error("Failed to start %s WS client: %s", name, e)

    async def stop_all(self) -> None:
        """Stop all 3 clients -- one client failing to stop cleanly must
        not prevent the other two from stopping."""
        for name, client in self._clients.items():
            try:
                await client.stop()
            except Exception as e:
                logger.error("Failed to stop %s WS client: %s", name, e)

    @property
    def status(self) -> dict[str, dict[str, bool]]:
        return {
            name: {"running": client.is_running, "connected": client.is_connected}
            for name, client in self._clients.items()
        }


def get_shared_stream_manager() -> MarketStreamManager:
    """Process-wide singleton, same lazy double-checked-locking pattern as
    get_shared_candle_stream_cache()/get_shared_multi_provider()."""
    global _shared_manager_instance
    if _shared_manager_instance is None:
        with _shared_manager_lock:
            if _shared_manager_instance is None:
                _shared_manager_instance = MarketStreamManager()
    return _shared_manager_instance
