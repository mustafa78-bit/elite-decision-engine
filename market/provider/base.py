"""Abstract provider interface for market data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Protocol

import pandas as pd


@dataclass
class OHLCVResult:
    symbol: str
    timeframe: str
    df: pd.DataFrame
    fetched_at: datetime

    @property
    def empty(self) -> bool:
        return self.df.empty

    @property
    def latest_close(self) -> float:
        if self.df.empty:
            return 0.0
        return float(self.df["close"].iloc[-1])


class DataProvider(Protocol):
    """Interface all data providers must implement."""

    def get_ohlcv(
        self,
        symbol: str = "BTC",
        timeframe: str = "1h",
        limit: int = 500,
    ) -> pd.DataFrame:
        ...

    def get_ticker(self, symbol: str) -> dict[str, Any]:
        ...

    def get_funding(self, symbol: str) -> dict[str, Any]:
        ...

    def get_open_interest(self, symbol: str) -> dict[str, Any]:
        ...

    def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        ...

    def get_trades(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        ...
