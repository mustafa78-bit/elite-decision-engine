from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pandas as pd

from exchange.models import Candle, Ticker


def normalize_candle_from_df(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    ts_col: str = "timestamp",
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    volume_col: str = "volume",
) -> list[Candle]:
    """Normalize a pandas DataFrame of candles to Candle objects."""
    result: list[Candle] = []
    for _, row in df.iterrows():
        ts_val = row.get(ts_col, 0)
        if isinstance(ts_val, (int, float)) and ts_val > 1e10:
            ts = datetime.fromtimestamp(ts_val / 1000, tz=timezone.utc)
        else:
            ts = datetime.now(timezone.utc)
        result.append(Candle(
            symbol=symbol,
            timeframe=timeframe,
            open=Decimal(str(row[open_col])),
            high=Decimal(str(row[high_col])),
            low=Decimal(str(row[low_col])),
            close=Decimal(str(row[close_col])),
            volume=Decimal(str(row[volume_col])),
            timestamp=ts,
        ))
    return result


def normalize_ticker(
    symbol: str,
    last: float,
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    volume_24h: Optional[float] = None,
    high_24h: Optional[float] = None,
    low_24h: Optional[float] = None,
    change_24h: Optional[float] = None,
) -> Ticker:
    """Create a normalized Ticker from raw values."""
    return Ticker(
        symbol=symbol,
        bid=Decimal(str(bid or last * 0.999)),
        ask=Decimal(str(ask or last * 1.001)),
        last=Decimal(str(last)),
        volume_24h=Decimal(str(volume_24h or 0)),
        high_24h=Decimal(str(high_24h or last)),
        low_24h=Decimal(str(low_24h or last)),
        change_24h=Decimal(str(change_24h or 0)),
    )


def merge_candles(
    candles_list: list[list[Candle]],
    sort_by_time: bool = True,
) -> list[Candle]:
    """Merge multiple candle lists into one sorted list."""
    merged: list[Candle] = []
    for candles in candles_list:
        merged.extend(candles)
    if sort_by_time:
        merged.sort(key=lambda c: c.timestamp)
    return merged


def deduplicate_candles(candles: list[Candle]) -> list[Candle]:
    """Remove candles with duplicate timestamps (keeps first)."""
    seen: set[int] = set()
    result: list[Candle] = []
    for c in candles:
        ts = int(c.timestamp.timestamp())
        if ts not in seen:
            seen.add(ts)
            result.append(c)
    return result
