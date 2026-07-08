from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from strategies.base import Strategy, StrategyResult

logger = logging.getLogger(__name__)


class TrendFollowStrategy(Strategy):
    """Follow EMA trend: LONG when price > EMA20 > EMA50, SHORT when opposite."""

    name = "trend_follow"

    def evaluate(self, symbol: str, market_data: Any) -> Optional[StrategyResult]:
        df = self._ensure_df(market_data)
        if df is None or len(df) < 50:
            return None

        close = float(df["close"].iloc[-1])
        ema20 = float(df["close"].ewm(span=20).mean().iloc[-1])
        ema50 = float(df["close"].ewm(span=50).mean().iloc[-1])

        if close > ema20 > ema50:
            confidence = min((close / ema50 - 1) * 500, 90)
            return StrategyResult(signal="LONG", confidence=round(confidence, 1), metadata={"ema20": ema20, "ema50": ema50})
        elif close < ema20 < ema50:
            confidence = min((ema50 / close - 1) * 500, 90)
            return StrategyResult(signal="SHORT", confidence=round(confidence, 1), metadata={"ema20": ema20, "ema50": ema50})
        return StrategyResult(signal="NEUTRAL", confidence=0, metadata={"ema20": ema20, "ema50": ema50})

    def description(self) -> str:
        return "EMA trend follower: LONG when price > EMA20 > EMA50, SHORT when opposite"

    @staticmethod
    def _ensure_df(data: Any) -> Optional[pd.DataFrame]:
        if isinstance(data, pd.DataFrame):
            return data
        return None


class MeanReversionStrategy(Strategy):
    """Mean reversion using RSI: SHORT when RSI > 70, LONG when RSI < 30."""

    name = "mean_reversion"

    def evaluate(self, symbol: str, market_data: Any) -> Optional[StrategyResult]:
        df = self._ensure_df(market_data)
        if df is None or len(df) < 20:
            return None

        close = df["close"].astype(float)
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])

        if current_rsi < 30:
            confidence = round((30 - current_rsi) * 3, 1)
            return StrategyResult(signal="LONG", confidence=min(confidence, 95), metadata={"rsi": current_rsi})
        elif current_rsi > 70:
            confidence = round((current_rsi - 70) * 3, 1)
            return StrategyResult(signal="SHORT", confidence=min(confidence, 95), metadata={"rsi": current_rsi})
        return StrategyResult(signal="NEUTRAL", confidence=0, metadata={"rsi": current_rsi})

    def description(self) -> str:
        return "RSI mean reversion: LONG when RSI < 30, SHORT when RSI > 70"

    @staticmethod
    def _ensure_df(data: Any) -> Optional[pd.DataFrame]:
        if isinstance(data, pd.DataFrame):
            return data
        return None
