"""Hyperliquid provider that delegates to existing HyperliquidCollector."""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from market_data.collector import HyperliquidCollector
from market_data.funding import FundingCollector
from market_data.open_interest import OpenInterestCollector

logger = logging.getLogger(__name__)


class HyperliquidProvider:
    """MIP provider wrapping existing Hyperliquid data collectors."""

    def __init__(
        self,
        collector: HyperliquidCollector | None = None,
        funding_collector: FundingCollector | None = None,
        oi_collector: OpenInterestCollector | None = None,
    ) -> None:
        self._collector = collector or HyperliquidCollector()
        self._funding = funding_collector or FundingCollector()
        self._oi = oi_collector or OpenInterestCollector()

    def get_ohlcv(
        self,
        symbol: str = "BTC",
        timeframe: str = "1h",
        limit: int = 500,
    ) -> pd.DataFrame:
        # get_funding()/get_open_interest() below both strip "USDT" before
        # calling their collectors -- this one didn't, so every ticker-style
        # symbol (e.g. "ETHUSDT", as scanner/core.py passes) hit Hyperliquid's
        # candleSnapshot with an unknown coin id and 500'd, while only
        # already-bare symbols like "BTC" ever worked.
        coin = symbol.replace("USDT", "")
        return self._collector.get_ohlcv(symbol=coin, timeframe=timeframe, limit=limit)

    def get_ticker(self, symbol: str) -> dict[str, Any]:
        df = self.get_ohlcv(symbol=symbol, limit=2)
        if df.empty:
            return {"symbol": symbol, "price": 0.0}
        return {
            "symbol": symbol,
            "price": float(df["close"].iloc[-1]),
            "open": float(df["open"].iloc[-1]),
            "high": float(df["high"].iloc[-1]),
            "low": float(df["low"].iloc[-1]),
            "volume": float(df["volume"].iloc[-1]),
        }

    def get_funding(self, symbol: str) -> dict[str, Any]:
        coin = symbol.replace("USDT", "")
        try:
            result = self._funding.fetch_for_symbol(coin)
            return {
                "symbol": symbol,
                "rate": result.rate if hasattr(result, "rate") else 0.0,
                "timestamp": str(result.timestamp) if hasattr(result, "timestamp") else "",
            }
        except Exception as e:
            logger.warning("Funding fetch failed for %s: %s", symbol, e)
            return {"symbol": symbol, "rate": 0.0, "error": str(e)}

    def get_open_interest(self, symbol: str) -> dict[str, Any]:
        coin = symbol.replace("USDT", "")
        try:
            # fetch_with_trend() returns a plain dict (keys: symbol, value,
            # trend, strength, timestamp), not an object -- hasattr() on a
            # dict for a non-existent attribute is always False, so this
            # previously discarded real data on every successful call.
            result = self._oi.fetch_with_trend(coin)
            return {
                "symbol": symbol,
                "open_interest": result.get("value", 0.0),
                "trend": result.get("trend", "unknown"),
            }
        except Exception as e:
            logger.warning("OI fetch failed for %s: %s", symbol, e)
            return {"symbol": symbol, "open_interest": 0.0, "error": str(e)}

    def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        return {"symbol": symbol, "bids": [], "asks": [], "depth": depth}

    def get_trades(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        return []
