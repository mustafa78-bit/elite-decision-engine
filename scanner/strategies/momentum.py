from __future__ import annotations

from typing import Any


class MomentumStrategy:
    """Score momentum opportunities using RSI and rate of change."""

    name = "momentum"

    def evaluate(self, asset: Any) -> tuple[float, list[str]]:
        indicators = asset.indicators
        features = asset.features
        signals: list[str] = []

        rsi = indicators.get("rsi", 50)

        score = 0.0

        if rsi >= 60:
            score += 0.4
            signals.append("RSI_BULLISH")
        elif rsi <= 40:
            score += 0.4
            signals.append("RSI_BEARISH")

        if rsi >= 55:
            score += 0.2 * ((rsi - 55) / 45)
        elif rsi <= 45:
            score += 0.2 * ((45 - rsi) / 45)

        momentum = features.get("momentum", "NEUTRAL")
        if momentum == "STRONG":
            score += 0.3
            signals.append("MOMENTUM_STRONG")

        if momentum == "OVERBOUGHT" and rsi > 75:
            signals.append("RSI_OVERBOUGHT")
        elif momentum == "OVERSOLD" and rsi < 25:
            signals.append("RSI_OVERSOLD")

        return round(min(score, 1.0), 4), signals
