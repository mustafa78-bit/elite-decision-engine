import logging
import time
from typing import Any, Optional

import pandas as pd
import requests

from market_data.models import OHLCVResult

logger = logging.getLogger(__name__)

# A flat 7200s (2h) threshold regardless of timeframe was actually calibrated
# for 1h candles specifically (2x its own 3600s period) and never revisited
# for other timeframes -- a 4h candle spends over half its real, un-stale
# lifecycle (2h-4h into the current candle) looking "stale" under that fixed
# number, so get_ohlcv(timeframe="4h") returned an empty DataFrame roughly
# half the time. That empty df then crashed market_data/mtf.py's
# IndicatorEngine.calculate() call (pandas_ta's df.ta.ema() chokes on an
# empty frame's integer-typed column index), caught by ScoringEngine.score()'s
# broad except and silently falling back to neutral scores for every signal
# hit during that window -- found live via real recurring "MARKET DATA
# ERROR: Can only use .str accessor..." log lines. Scale with the timeframe's
# own candle period instead (2x, preserving the existing 1h behavior exactly).
_CANDLE_SECONDS: dict[str, int] = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800,
}
_DEFAULT_CANDLE_SECONDS = 3600


def _stale_threshold_seconds(timeframe: str) -> int:
    return _CANDLE_SECONDS.get(timeframe, _DEFAULT_CANDLE_SECONDS) * 2


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
        if age_seconds > _stale_threshold_seconds(timeframe):
            logger.warning(
                "Stale market data for %s %s: latest candle is %.1f hours old",
                symbol, timeframe, age_seconds / 3600,
            )
            return pd.DataFrame()

        return df.tail(limit).reset_index(drop=True)

    def get_ohlcv_result(self, symbol: str = "BTC", timeframe: str = "1h", limit: int = 500) -> OHLCVResult:
        df = self.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        return OHLCVResult.from_dataframe(df, symbol=symbol, timeframe=timeframe)
