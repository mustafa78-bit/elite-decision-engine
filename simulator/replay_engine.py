from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import pandas as pd

from simulator.models import MarketRegime, SimulatedCandle

logger = logging.getLogger(__name__)

SUPPORTED_TIMEFRAMES = frozenset({"1m", "5m", "15m", "1h", "4h", "1d"})
TIMEFRAME_MS = {
    "1m": 60000,
    "5m": 300000,
    "15m": 900000,
    "1h": 3600000,
    "4h": 14400000,
    "1d": 86400000,
}


class MarketReplayEngine:
    def __init__(self, data_provider: Optional[Any] = None):
        self._data_provider = data_provider
        self._candles: list[SimulatedCandle] = []
        self._index: int = 0
        self._symbol: str = ""
        self._timeframe: str = "1h"
        self._listeners: list[Callable[[SimulatedCandle], None]] = []
        self._regime_listeners: list[Callable[[MarketRegime], None]] = []
        self._regime_cache: dict[int, MarketRegime] = {}

    @property
    def current(self) -> Optional[SimulatedCandle]:
        if 0 <= self._index < len(self._candles):
            return self._candles[self._index]
        return None

    @property
    def previous(self) -> Optional[SimulatedCandle]:
        if 1 <= self._index < len(self._candles):
            return self._candles[self._index - 1]
        return None

    @property
    def index(self) -> int:
        return self._index

    @property
    def total(self) -> int:
        return len(self._candles)

    @property
    def progress(self) -> float:
        if self.total == 0:
            return 0.0
        return self._index / self.total

    @property
    def symbol(self) -> str:
        return self._symbol

    def on_candle(self, listener: Callable[[SimulatedCandle], None]) -> None:
        self._listeners.append(listener)

    def on_regime_change(self, listener: Callable[[MarketRegime], None]) -> None:
        self._regime_listeners.append(listener)

    def load(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data: Optional[pd.DataFrame] = None,
    ) -> int:
        self._symbol = symbol.upper()
        self._timeframe = timeframe
        self._index = 0
        self._candles = []

        if data is not None and not data.empty:
            df = data
        elif self._data_provider is not None:
            df = self._fetch_data(symbol, timeframe, start_date, end_date)
        else:
            df = self._generate_synthetic(symbol, timeframe, start_date, end_date)

        if df is None or df.empty:
            logger.warning("No data loaded for %s %s", symbol, timeframe)
            return 0

        self._candles = self._df_to_candles(df)
        logger.info(
            "Loaded %s candles for %s %s (%s -> %s)",
            len(self._candles),
            symbol,
            timeframe,
            self._candles[0].timestamp if self._candles else "?",
            self._candles[-1].timestamp if self._candles else "?",
        )
        return len(self._candles)

    def step(self) -> Optional[SimulatedCandle]:
        if self._index >= len(self._candles):
            return None
        candle = self._candles[self._index]
        self._index += 1
        for listener in self._listeners:
            listener(candle)
        regime = self._detect_regime(candle)
        cached = self._regime_cache.get(self._index)
        if cached is not None and cached != regime:
            for listener in self._regime_listeners:
                listener(regime)
        self._regime_cache[self._index] = regime
        return candle

    def step_back(self) -> Optional[SimulatedCandle]:
        if self._index <= 0:
            return None
        self._index -= 1
        return self._candles[self._index]

    def seek(self, candle_index: int) -> Optional[SimulatedCandle]:
        if candle_index < 0 or candle_index >= len(self._candles):
            return None
        self._index = candle_index
        return self._candles[self._index]

    def seek_to_timestamp(self, timestamp: int) -> Optional[SimulatedCandle]:
        for i, c in enumerate(self._candles):
            if c.timestamp >= timestamp:
                self._index = i
                return c
        return None

    def get_range(self, start_index: int, count: int) -> list[SimulatedCandle]:
        return self._candles[start_index : start_index + count]

    def get_all(self) -> list[SimulatedCandle]:
        return list(self._candles)

    def reset(self) -> None:
        self._index = 0
        self._regime_cache.clear()

    def _detect_regime(self, candle: SimulatedCandle) -> MarketRegime:
        if self._index < 20:
            return MarketRegime.SIDEWAYS
        window = self._candles[max(0, self._index - 20) : self._index]
        closes = [c.close for c in window]
        if len(closes) < 5:
            return MarketRegime.SIDEWAYS
        first = closes[0]
        last = closes[-1]
        change = (last - first) / first
        high = max(c.high for c in window)
        low = min(c.low for c in window)
        range_pct = (high - low) / first
        if range_pct > 0.15:
            return MarketRegime.VOLATILE
        if change > 0.05:
            return MarketRegime.BULL
        if change < -0.05:
            return MarketRegime.BEAR
        return MarketRegime.SIDEWAYS

    def _fetch_data(
        self, symbol: str, timeframe: str, start_date: Optional[str], end_date: Optional[str]
    ) -> Optional[pd.DataFrame]:
        try:
            if hasattr(self._data_provider, "get_ohlcv"):
                coin = symbol.replace("USDT", "")
                df = self._data_provider.get_ohlcv(symbol=coin, timeframe=timeframe, limit=1000)
                if df is not None and not df.empty:
                    return df
            if hasattr(self._data_provider, "fetch_historical"):
                kwargs = {"symbol": symbol, "timeframe": timeframe}
                if start_date:
                    kwargs["start"] = start_date
                if end_date:
                    kwargs["end"] = end_date
                return self._data_provider.fetch_historical(**kwargs)
        except Exception as e:
            logger.warning("Data fetch failed for %s %s: %s", symbol, timeframe, e)
        return None

    def _generate_synthetic(
        self, symbol: str, timeframe: str, start_date: Optional[str], end_date: Optional[str]
    ) -> pd.DataFrame:
        import random

        logger.info("Generating synthetic data for %s %s", symbol, timeframe)
        start_ts: int
        end_ts: int
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        if start_date:
            try:
                start_ts = int(datetime.fromisoformat(start_date).timestamp() * 1000)
            except ValueError:
                start_ts = now - 86400000 * 30
        else:
            start_ts = now - 86400000 * 30
        if end_date:
            try:
                end_ts = int(datetime.fromisoformat(end_date).timestamp() * 1000)
            except ValueError:
                end_ts = now
        else:
            end_ts = now

        ms = TIMEFRAME_MS.get(timeframe, 3600000)
        times = list(range(start_ts, end_ts, ms))
        base = 30000.0 if "BTC" in symbol else (2000.0 if "ETH" in symbol else 100.0)
        data: list[dict[str, Any]] = []
        price = base
        drift = 0.0001
        volatility = 0.02
        seed = hash(symbol) % 10000
        rng = random.Random(seed)
        for t in times:
            ret = rng.gauss(drift, volatility)
            price *= 1 + ret
            high = price * (1 + abs(rng.gauss(0, volatility * 0.5)))
            low = price * (1 - abs(rng.gauss(0, volatility * 0.5)))
            volume = rng.uniform(100, 10000)
            data.append({
                "timestamp": t,
                "open": round(price / (1 + ret), 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(price, 2),
                "volume": round(volume, 2),
            })
        return pd.DataFrame(data)

    def _df_to_candles(self, df: pd.DataFrame) -> list[SimulatedCandle]:
        candles: list[SimulatedCandle] = []
        ts_col = None
        for col in ["timestamp", "time", "date", "t"]:
            if col in df.columns:
                ts_col = col
                break
        for _, row in df.iterrows():
            ts = row[ts_col] if ts_col else 0
            if isinstance(ts, str):
                try:
                    ts = int(datetime.fromisoformat(ts).timestamp() * 1000)
                except ValueError:
                    ts = 0
            candles.append(SimulatedCandle(
                timestamp=int(ts),
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                volume=float(row.get("volume", 0)),
            ))
        return candles
