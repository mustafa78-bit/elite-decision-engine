from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OHLCV:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class OHLCVResult:
    symbol: str
    timeframe: str
    candles: tuple[OHLCV, ...]
    fetched_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

    @property
    def empty(self) -> bool:
        return len(self.candles) == 0

    @property
    def latest(self) -> Optional[OHLCV]:
        if self.candles:
            return self.candles[-1]
        return None

    @property
    def is_stale(self, max_age_seconds: float = 7200.0) -> bool:
        if not self.candles:
            return True
        latest_ts = self.candles[-1].timestamp
        if latest_ts > 1e12:
            latest_ts = latest_ts / 1000
        age = self.fetched_at - latest_ts
        return age > max_age_seconds

    def to_dataframe(self):
        import pandas as pd
        if not self.candles:
            return pd.DataFrame()
        records = [
            {
                "timestamp": c.timestamp,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in self.candles
        ]
        return pd.DataFrame(records)

    @classmethod
    def from_dataframe(cls, df: Any, symbol: str, timeframe: str) -> OHLCVResult:
        if df is None or (hasattr(df, "empty") and df.empty):
            return cls(symbol=symbol, timeframe=timeframe, candles=())
        candles = []
        for _, row in df.iterrows():
            candles.append(OHLCV(
                timestamp=int(row.get("timestamp", 0)),
                open=float(row.get("open", 0.0)),
                high=float(row.get("high", 0.0)),
                low=float(row.get("low", 0.0)),
                close=float(row.get("close", 0.0)),
                volume=float(row.get("volume", 0.0)),
            ))
        return cls(
            symbol=symbol,
            timeframe=timeframe,
            candles=tuple(candles),
        )


def validate_ohlcv_result(result: OHLCVResult) -> list[str]:
    errors: list[str] = []
    if result.empty:
        errors.append("No candles")
        return errors
    for i, c in enumerate(result.candles):
        if c.open <= 0:
            errors.append(f"Candle {i}: non-positive open ({c.open})")
        if c.high < c.low:
            errors.append(f"Candle {i}: high ({c.high}) < low ({c.low})")
        if c.high < c.open or c.high < c.close:
            errors.append(f"Candle {i}: high ({c.high}) below open/close")
        if c.low > c.open or c.low > c.close:
            errors.append(f"Candle {i}: low ({c.low}) above open/close")
        if c.volume < 0:
            errors.append(f"Candle {i}: negative volume ({c.volume})")
    return errors


def check_timestamp_freshness(
    result: OHLCVResult,
    now: Optional[float] = None,
    max_age_seconds: float = 7200.0,
) -> tuple[bool, Optional[str]]:
    if not result.candles:
        return False, "No candle data to check freshness"
    now = now or datetime.now(timezone.utc).timestamp()
    latest_ts = result.candles[-1].timestamp
    if latest_ts > 1e12:
        latest_ts = latest_ts / 1000
    age = now - latest_ts
    if age > max_age_seconds:
        return False, f"Latest candle is {age / 3600:.1f}h old (max {max_age_seconds / 3600:.1f}h)"
    return True, None
