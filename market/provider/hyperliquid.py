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
        collector: Optional[HyperliquidCollector] = None,
        funding_collector: Optional[FundingCollector] = None,
        oi_collector: Optional[OpenInterestCollector] = None,
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
        return self._collector.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

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
            result = self._oi.fetch_with_trend(coin)
            return {
                "symbol": symbol,
                "open_interest": result.open_interest if hasattr(result, "open_interest") else 0.0,
                "trend": result.trend if hasattr(result, "trend") else "UNKNOWN",
            }
        except Exception as e:
            logger.warning("OI fetch failed for %s: %s", symbol, e)
            return {"symbol": symbol, "open_interest": 0.0, "error": str(e)}

    def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        return {"symbol": symbol, "bids": [], "asks": [], "depth": depth}

    def get_trades(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        return []
