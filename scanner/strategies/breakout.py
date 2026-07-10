from __future__ import annotations

from typing import Any

import pandas as pd


class BreakoutStrategy:
    """Score breakout opportunities using price vs EMA and volume confirmation."""

    name = "breakout"

    MIN_LOOKBACK = 20

    def evaluate(self, asset: Any) -> tuple[float, list[str]]:
        indicators = asset.indicators
        signals: list[str] = []

        ohlcv = asset.ohlcv
        if ohlcv is None or len(ohlcv) < self.MIN_LOOKBACK:
            return 0.0, signals

        ema20 = indicators.get("ema20", 0)
        price = asset.price
        if ema20 <= 0 or price <= 0:
            return 0.0, signals

        closes = ohlcv["close"].values
        volumes = ohlcv["volume"].values

        recent = closes[-5:]
        prior = closes[-self.MIN_LOOKBACK:-5]

        score = 0.0

        if len(prior) > 0:
            prior_max = float(max(prior))
            if price > prior_max and price > ema20:
                score += 0.5
                signals.append("PRICE_BREAKOUT_HIGH")

            prior_min = float(min(prior))
            if price < prior_min and price < ema20:
                score += 0.5
                signals.append("PRICE_BREAKOUT_LOW")

        avg_volume = float(volumes[-self.MIN_LOOKBACK:].mean())
        current_volume = float(volumes[-1])
        if avg_volume > 0 and current_volume > avg_volume * 1.5:
            score += 0.3
            signals.append("HIGH_VOLUME_CONFIRMATION")

        if all(recent > ema20) and len(recent) > 0 and float(recent[0]) <= ema20:
            score += 0.2
            signals.append("EMA_CROSSOVER")

        return round(min(score, 1.0), 4), signals
