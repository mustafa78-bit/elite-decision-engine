from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass
class OHLCVData:
    symbol: str
    timeframe: str
    df: pd.DataFrame
    latest_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_stale: bool = False
    age_seconds: float = 0.0

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, symbol: str = "", timeframe: str = "1h") -> OHLCVData:
        if df.empty:
            return cls(symbol=symbol, timeframe=timeframe, df=df)
        latest = float(df["close"].iloc[-1])
        return cls(
            symbol=symbol,
            timeframe=timeframe,
            df=df,
            latest_price=latest,
        )

    @property
    def empty(self) -> bool:
        return self.df.empty

    def __len__(self) -> int:
        return len(self.df)
