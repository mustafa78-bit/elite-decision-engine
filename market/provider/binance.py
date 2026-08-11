"""Binance provider that implements DataProvider using Binance public REST API."""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
import requests

from market.provider.base import DataProvider
from market.provider.hyperliquid import HyperliquidProvider

logger = logging.getLogger(__name__)

_STALE_THRESHOLD_SECONDS = 7200  # 2 hours


class BinanceProvider:
    """MIP provider using Binance public REST API directly."""

    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2.0

    def __init__(
        self,
        fallback_provider: DataProvider | None = None,
        timeout: int = 20,
    ) -> None:
        self.timeout = timeout
        self._fallback = fallback_provider or HyperliquidProvider()
        self._session = requests.Session()

    def get_ohlcv(
        self,
        symbol: str = "BTC",
        timeframe: str = "1h",
        limit: int = 500,
    ) -> pd.DataFrame:
        """Fetch OHLCV klines from Binance's public REST API."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self._session.get(
                    "https://api.binance.com/api/v3/klines",
                    params={
                        "symbol": symbol,
                        "interval": timeframe,
                        "limit": limit,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                klines = response.json()
                if not isinstance(klines, list):
                    raise ValueError(f"Expected list response, got {type(klines).__name__}")
                logger.debug(
                    "BinanceProvider attempt %s/%s succeeded for %s %s",
                    attempt, self.MAX_RETRIES, symbol, timeframe,
                )
                break
            except requests.Timeout as e:
                logger.warning(
                    "Timeout on attempt %s/%s for %s %s: %s",
                    attempt, self.MAX_RETRIES, symbol, timeframe, e,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.BACKOFF_FACTOR ** attempt)
                    continue
                raise
            except (requests.RequestException, ValueError) as e:
                logger.warning(
                    "Request failed on attempt %s/%s for %s %s: %s",
                    attempt, self.MAX_RETRIES, symbol, timeframe, e,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.BACKOFF_FACTOR ** attempt)
                    continue
                raise

        if not klines:
            logger.warning("No candle data returned for %s %s", symbol, timeframe)
            return pd.DataFrame()

        df = pd.DataFrame(klines)

        if df.empty:
            logger.warning("Empty DataFrame after decode for %s %s", symbol, timeframe)
            return pd.DataFrame()

        if df.shape[1] < 6:
            logger.warning("Binance API response has fewer than 6 columns: %s", df.shape[1])
            return pd.DataFrame()

        # Keep first 6 columns: Open time, Open, High, Low, Close, Volume
        df = df.iloc[:, :6]
        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]

        df["timestamp"] = df["timestamp"].astype('int64')
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        if df["close"].isna().all():
            return pd.DataFrame()

        latest_ts = df["timestamp"].max()
        now_seconds = time.time()
        if latest_ts > 1e12:
            latest_ts = latest_ts / 1000
        age_seconds = now_seconds - latest_ts
        if age_seconds > _STALE_THRESHOLD_SECONDS:
            logger.warning(
                "Stale market data for %s %s: latest candle is %.1f hours old",
                symbol, timeframe, age_seconds / 3600,
            )
            return pd.DataFrame()

        return df.tail(limit).reset_index(drop=True)

    def get_ticker(self, symbol: str) -> dict[str, Any]:
        """Derive the current ticker info from klines."""
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
        """Delegate to fallback provider."""
        return self._fallback.get_funding(symbol)

    def get_open_interest(self, symbol: str) -> dict[str, Any]:
        """Delegate to fallback provider."""
        return self._fallback.get_open_interest(symbol)

    def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        """Delegate to fallback provider."""
        return self._fallback.get_orderbook(symbol, depth=depth)

    def get_trades(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        """Delegate to fallback provider."""
        return self._fallback.get_trades(symbol, limit=limit)
