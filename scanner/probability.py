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
        side: str = "LONG",
    ) -> tuple[float, list[str]]:
        base = composite_score * 100
        signals: list[str] = []

        prob = base

        if side == "LONG":
            aligned_trend = trend_score
            aligned_breakout = breakout_score
            aligned_reversal = reversal_score
        else:
            aligned_trend = -trend_score
            aligned_breakout = -breakout_score
            aligned_reversal = -reversal_score

        if aligned_trend > 0.5:
            prob += 10
            signals.append("STRONG_TREND_BOOST")
        elif aligned_trend > 0.3:
            prob += 5
            signals.append("MODERATE_TREND_BOOST")

        if aligned_breakout > 0.5:
            prob += 8
            signals.append("BREAKOUT_BOOST")

        if liquidity_score > 0.5:
            prob += 5
            signals.append("LIQUIDITY_BOOST")

        if aligned_reversal > 0.5:
            prob -= 5
            signals.append("REVERSAL_PENALTY")

        if side == "LONG":
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
        else: # "SHORT"
            if btc_trend == "BEARISH":
                prob += 5
                signals.append("BTC_BEARISH_CONTEXT")
            elif btc_trend == "BULLISH":
                prob -= 5
                signals.append("BTC_BULLISH_PENALTY")

            if funding_level == "HIGH_SHORT":
                prob -= 5
                signals.append("HIGH_FUNDING_SHORT_PENALTY")
            elif funding_level == "HIGH_LONG":
                prob += 3
                signals.append("HIGH_FUNDING_LONG_EDGE")

            if fear_greed_value is not None:
                if 60 <= fear_greed_value <= 75:
                    prob += 5
                    signals.append("GREED_SHORTING_OPPORTUNITY")
                elif fear_greed_value < 20:
                    prob -= 5
                    signals.append("EXTREME_FEAR_CAUTION")
                elif fear_greed_value > 85:
                    prob += 8
                    signals.append("EXTREME_GREED_OPPORTUNITY")

        prob = max(0.0, min(100.0, round(prob, 2)))
        return prob, signals
