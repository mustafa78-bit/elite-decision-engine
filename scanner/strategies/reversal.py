from __future__ import annotations

from typing import Any

import pandas as pd


class ReversalStrategy:
    """Score reversal opportunities using RSI extremes and divergence."""

    name = "reversal"

    MIN_LOOKBACK = 14

    def evaluate(self, asset: Any) -> tuple[float, list[str]]:
        indicators = asset.indicators
        features = asset.features
        signals: list[str] = []

        ohlcv = asset.ohlcv
        if ohlcv is None or len(ohlcv) < self.MIN_LOOKBACK:
            return 0.0, signals

        rsi = indicators.get("rsi", 50)
        price = asset.price

        score_long = 0.0
        score_short = 0.0

        momentum = features.get("momentum", "NEUTRAL")

        if momentum == "OVERSOLD":
            score_long += 0.5
            signals.append("OVERSOLD_REVERSAL")
            if rsi < 25:
                score_long += 0.2
                signals.append("EXTREME_OVERSOLD")
        elif momentum == "OVERBOUGHT":
            score_short += 0.5
            signals.append("OVERBOUGHT_REVERSAL")
            if rsi > 75:
                score_short += 0.2
                signals.append("EXTREME_OVERBOUGHT")

        closes = ohlcv["close"].values
        price_high = max(closes[-self.MIN_LOOKBACK:])
        price_low = min(closes[-self.MIN_LOOKBACK:])

        if momentum == "OVERBOUGHT" and price >= price_high * 0.98:
            score_short += 0.3
            signals.append("PRICE_AT_RESISTANCE")
        elif momentum == "OVERSOLD" and price <= price_low * 1.02:
            score_long += 0.3
            signals.append("PRICE_AT_SUPPORT")

        if score_long >= score_short:
            return round(min(score_long, 1.0), 4), signals
        else:
            return -round(min(score_short, 1.0), 4), signals
