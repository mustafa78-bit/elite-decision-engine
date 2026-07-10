"""ProbabilityEngine — estimates probability of trade success."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ProbabilityEngine:
    """Estimate probability of success for a given opportunity."""

    def estimate(
        self,
        composite_score: float,
        trend_score: float = 0.0,
        momentum_score: float = 0.0,
        breakout_score: float = 0.0,
        reversal_score: float = 0.0,
        liquidity_score: float = 0.0,
        btc_trend: Optional[str] = None,
        funding_level: Optional[str] = None,
        fear_greed_value: Optional[float] = None,
    ) -> tuple[float, list[str]]:
        base = composite_score * 100
        signals: list[str] = []

        prob = base

        if trend_score > 0.5:
            prob += 10
            signals.append("STRONG_TREND_BOOST")
        elif trend_score > 0.3:
            prob += 5
            signals.append("MODERATE_TREND_BOOST")

        if breakout_score > 0.5:
            prob += 8
            signals.append("BREAKOUT_BOOST")

        if liquidity_score > 0.5:
            prob += 5
            signals.append("LIQUIDITY_BOOST")

        if reversal_score > 0.5:
            prob -= 5
            signals.append("REVERSAL_PENALTY")

        if btc_trend == "BULLISH":
            prob += 5
            signals.append("BTC_BULLISH_CONTEXT")
        elif btc_trend == "BEARISH":
            prob -= 5
            signals.append("BTC_BEARISH_PENALTY")

        if funding_level == "HIGH_LONG":
            prob -= 5
            signals.append("HIGH_FUNDING_LONG_PENALTY")
        elif funding_level == "HIGH_SHORT":
            prob += 3
            signals.append("HIGH_FUNDING_SHORT_EDGE")

        if fear_greed_value is not None:
            if 25 <= fear_greed_value <= 40:
                prob += 5
                signals.append("FEAR_BUYING_OPPORTUNITY")
            elif fear_greed_value > 80:
                prob -= 5
                signals.append("EXTREME_GREED_CAUTION")
            elif fear_greed_value < 15:
                prob += 8
                signals.append("EXTREME_FEAR_OPPORTUNITY")

        prob = max(0.0, min(100.0, round(prob, 2)))
        return prob, signals
