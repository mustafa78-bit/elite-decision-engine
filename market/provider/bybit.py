"""Bybit provider that implements DataProvider using Bybit's public V5 REST API.

Third CEX data source alongside Hyperliquid/Binance -- added to spread
FIXED_COIN_UNIVERSE's real market-data fetch load across another provider
after Hyperliquid kept showing real, recurring 429s even with the existing
Hyperliquid/Binance split (observed live across multiple hourly monitoring
windows 2026-08-18/19). Bybit's V5 unified API was chosen over Gate.io/MEXC
(lower-liquidity altcoin focus, not needed for this majors-only universe) and
over on-chain DEX alternatives (dYdX/Drift/Vertex/GMX -- this app already
treats Hyperliquid as a plain read-only market-data REST API, not an
on-chain venue with wallet/gas concerns, so a DEX alternative would add
integration complexity for no real benefit over another CEX).
"""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
import requests

from market.provider.base import DataProvider
from market.provider.hyperliquid import HyperliquidProvider

logger = logging.getLogger(__name__)

_STALE_THRESHOLD_SECONDS = 7200  # 2 hours -- see market_data/collector.py's
# per-timeframe version of this same staleness check (row #113 of this
# session's task board) for why a flat value is really only correct for 1h;
# left flat here to match BinanceProvider's existing convention rather than
# introducing yet another divergent staleness implementation in one PR.

# Bybit V5's kline "interval" values are plain minute-counts or a single
# calendar-unit letter, not the "15m"/"1h"/"4h"/"1d" strings this app uses
# everywhere else (matching Binance's convention). Only the timeframes this
# app actually requests (SCANNER_TIMEFRAME default "15m", MTFEngine's
# "15m"/"1h"/"4h", dashboards' "1h"/"4h"/"1d") are mapped; an unmapped
# timeframe raises rather than silently guessing.
_INTERVAL_MAP: dict[str, str] = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "4h": "240",
    "1d": "D",
    "1w": "W",
}


class BybitProvider:
    """DataProvider implementation using Bybit's public V5 REST API."""

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
        """Fetch OHLCV klines from Bybit's public V5 REST API."""
        interval = _INTERVAL_MAP.get(timeframe)
        if interval is None:
            raise ValueError(f"Unsupported timeframe for BybitProvider: {timeframe!r}")

        # Bybit's "linear" category (USDT-margined perpetuals) matches this
        # app's "XUSDT" symbol convention directly -- FIXED_COIN_UNIVERSE
        # entries are already in Bybit's exact symbol format, no suffix
        # stripping/adding needed (unlike Hyperliquid's bare-ticker convention).
        klines: list[list[Any]] = []
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self._session.get(
                    "https://api.bybit.com/v5/market/kline",
                    params={
                        "category": "linear",
                        "symbol": symbol,
                        "interval": interval,
                        "limit": limit,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("retCode") != 0:
                    raise ValueError(f"Bybit API error: {data.get('retMsg')}")
                klines = data.get("result", {}).get("list", [])
                logger.debug(
                    "BybitProvider attempt %s/%s succeeded for %s %s",
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

        # Bybit V5 returns klines newest-first (descending startTime) --
        # every other provider/caller in this app assumes ascending
        # (oldest-first, latest candle at .iloc[-1]), so reverse before
        # anything downstream sees it.
        klines = list(reversed(klines))

        df = pd.DataFrame(klines)
        if df.empty or df.shape[1] < 6:
            logger.warning("Bybit API response has fewer than 6 columns: %s", df.shape[1] if not df.empty else 0)
            return pd.DataFrame()

        # Kline row shape: [startTime, open, high, low, close, volume, turnover]
        df = df.iloc[:, :6]
        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]

        df["timestamp"] = df["timestamp"].astype("int64")
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
