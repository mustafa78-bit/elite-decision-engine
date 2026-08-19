from __future__ import annotations

from typing import Any

from config import TREND_OVEREXTENSION_MULTIPLIER, TREND_OVEREXTENSION_PCT_THRESHOLD


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

        score_long = 0.0
        score_short = 0.0

        if ema20 > ema50 > ema200:
            score_long += 0.8
            signals.append("BULLISH_TREND_ALIGNED")
        elif ema20 > ema50:
            score_long += 0.5
            signals.append("BULLISH_TREND_WEAK")
        elif ema20 < ema50 < ema200:
            score_short += 0.8
            signals.append("BEARISH_TREND_ALIGNED")
        elif ema20 < ema50:
            score_short += 0.5
            signals.append("BEARISH_TREND_WEAK")

        trend = features.get("trend", "NEUTRAL")
        if trend == "BULLISH":
            score_long += 0.2
            signals.append("FEATURE_BULLISH")
        elif trend == "BEARISH":
            score_short += 0.2
            signals.append("FEATURE_BEARISH")

        # Overextension guard -- EMA order alone can't tell a healthy trend
        # from one that's already vertical and due for a pullback. Applied
        # to whichever side is currently winning, not both blindly, so it
        # only discounts the score it actually risks overstating.
        price = getattr(asset, "price", 0) or 0
        if price > 0 and ema20 > 0:
            extension_pct = abs(price - ema20) / ema20 * 100
            if extension_pct > TREND_OVEREXTENSION_PCT_THRESHOLD:
                signals.append("TREND_OVEREXTENDED")
                if score_long >= score_short:
                    score_long *= TREND_OVEREXTENSION_MULTIPLIER
                else:
                    score_short *= TREND_OVEREXTENSION_MULTIPLIER

        if score_long >= score_short:
            return round(min(score_long, 1.0), 4), signals
        else:
            return -round(min(score_short, 1.0), 4), signals
