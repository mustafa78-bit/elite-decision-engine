"""Market data streaming package for real-time WebSocket feeds."""

from market.stream.binance_ws import BinanceWSClient
from market.stream.binance_ws import normalize_stream_symbol as normalize_binance_stream_symbol
from market.stream.bybit_ws import BybitWSClient
from market.stream.bybit_ws import normalize_stream_symbol as normalize_bybit_stream_symbol
from market.stream.cache import CandleStreamCache, get_shared_candle_stream_cache, normalize_symbol, normalize_timeframe
from market.stream.hyperliquid_ws import HyperliquidWSClient
from market.stream.hyperliquid_ws import normalize_stream_symbol as normalize_hyperliquid_stream_symbol
from market.stream.manager import MarketStreamManager, get_shared_stream_manager

__all__ = [
    "CandleStreamCache",
    "get_shared_candle_stream_cache",
    "BinanceWSClient",
    "BybitWSClient",
    "HyperliquidWSClient",
    "MarketStreamManager",
    "get_shared_stream_manager",
    "normalize_symbol",
    "normalize_timeframe",
    "normalize_binance_stream_symbol",
    "normalize_bybit_stream_symbol",
    "normalize_hyperliquid_stream_symbol",
]
