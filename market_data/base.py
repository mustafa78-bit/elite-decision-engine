from __future__ import annotations

import logging
from typing import Any, Optional, Protocol, runtime_checkable

from market_data.models import OHLCVResult

logger = logging.getLogger(__name__)


class CollectorProtocol(Protocol):
    def get_ohlcv(self, symbol: str = "BTC", timeframe: str = "1h", limit: int = 500) -> Any:
        ...


class DataProvider(Protocol):
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> OHLCVResult:
        ...


@runtime_checkable
class IntelligenceProvider(Protocol):
    def fetch_all(self) -> Any:
        ...

    def fetch_for_symbol(self, symbol: str) -> Optional[Any]:
        ...

    def check_freshness(self, symbol: str) -> dict:
        ...


def to_ohlcv_result(
    collector: CollectorProtocol,
    symbol: str,
    timeframe: str,
    limit: int = 500,
) -> OHLCVResult:
    try:
        df = collector.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        return OHLCVResult.from_dataframe(df, symbol=symbol, timeframe=timeframe)
    except Exception as e:
        logger.warning("Failed to fetch OHLCV for %s %s: %s", symbol, timeframe, e)
        return OHLCVResult(symbol=symbol, timeframe=timeframe, candles=())
