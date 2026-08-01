import logging
import time
from typing import Any, Optional

import requests
import pandas as pd

from market_data.models import OHLCVResult

logger = logging.getLogger(__name__)

_STALE_THRESHOLD_SECONDS = 7200  # 2 hours


class HyperliquidCollector:
    BASE_URL = "https://api.hyperliquid.xyz/info"
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2.0

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._session = requests.Session()

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):

        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": timeframe,
                "startTime": 0,
            },
        }

        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self._session.post(
                    self.BASE_URL,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                candles = response.json()
                if not isinstance(candles, list):
                    raise ValueError(f"Expected list response, got {type(candles).__name__}")
                logger.debug(
                    "Collector attempt %s/%s succeeded for %s %s",
                    attempt, self.MAX_RETRIES, symbol, timeframe,
                )
                break
            except requests.Timeout as e:
                last_error = e
                logger.warning(
                    "Timeout on attempt %s/%s for %s %s: %s",
                    attempt, self.MAX_RETRIES, symbol, timeframe, e,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.BACKOFF_FACTOR ** attempt)
                    continue
                raise
            except (requests.RequestException, ValueError) as e:
                last_error = e
                logger.warning(
                    "Request failed on attempt %s/%s for %s %s: %s",
                    attempt, self.MAX_RETRIES, symbol, timeframe, e,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.BACKOFF_FACTOR ** attempt)
                    continue
                raise

        if not candles:
            logger.warning("No candle data returned for %s %s", symbol, timeframe)
            return pd.DataFrame()

        df = pd.DataFrame(candles)

        if df.empty:
            logger.warning("Empty DataFrame after decode for %s %s", symbol, timeframe)
            return pd.DataFrame()

        df = df.rename(columns={
            "t": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
        })

        required = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"API response missing required columns: {missing}")

        df = df[required]

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

    def get_ohlcv_result(self, symbol: str = "BTC", timeframe: str = "1h", limit: int = 500) -> OHLCVResult:
        df = self.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        return OHLCVResult.from_dataframe(df, symbol=symbol, timeframe=timeframe)
