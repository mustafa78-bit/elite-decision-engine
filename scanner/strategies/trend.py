from __future__ import annotations

from typing import Any


class TrendStrategy:
    """Score trend-following opportunities using EMA alignment."""

    name = "trend"

    def evaluate(self, asset: Any) -> tuple[float, list[str]]:
        indicators = asset.indicators
        features = asset.features
        signals: list[str] = []

        ema20 = indicators.get("ema20", 0)
        ema50 = indicators.get("ema50", 0)
        ema200 = indicators.get("ema200", 0)

        if ema20 <= 0 or ema50 <= 0:
            return 0.0, signals

        score = 0.0

        if ema20 > ema50 > ema200:
            score += 0.8
            signals.append("BULLISH_TREND_ALIGNED")
        elif ema20 > ema50:
            score += 0.5
            signals.append("BULLISH_TREND_WEAK")
        elif ema20 < ema50 < ema200:
            score += 0.8
            signals.append("BEARISH_TREND_ALIGNED")
        elif ema20 < ema50:
            score += 0.5
            signals.append("BEARISH_TREND_WEAK")

        trend = features.get("trend", "NEUTRAL")
        if trend in ("BULLISH",):
            score += 0.2
            signals.append("FEATURE_BULLISH")
        elif trend in ("BEARISH",):
            score += 0.2
            signals.append("FEATURE_BEARISH")

        return round(min(score, 1.0), 4), signals
