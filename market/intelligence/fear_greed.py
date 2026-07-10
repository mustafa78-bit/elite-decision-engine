"""Fear & Greed Index — computed from market conditions when no external API is available."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FearGreedService:
    """Compute Fear & Greed index from available market data."""

    def compute(
        self,
        rsi: Optional[float] = None,
        btc_trend: Optional[str] = None,
        volatility_score: Optional[float] = None,
        funding_rate: Optional[float] = None,
    ) -> dict[str, Any]:
        score = 50.0
        signals: list[str] = []

        if rsi is not None:
            if rsi < 30:
                score -= 20
                signals.append("OVERSOLD_RSI")
            elif rsi < 40:
                score -= 10
                signals.append("LOW_RSI")
            elif rsi > 70:
                score += 20
                signals.append("OVERBOUGHT_RSI")
            elif rsi > 60:
                score += 10
                signals.append("HIGH_RSI")

        if btc_trend == "BEARISH":
            score -= 10
            signals.append("BTC_BEARISH")
        elif btc_trend == "BULLISH":
            score += 10
            signals.append("BTC_BULLISH")

        if volatility_score is not None:
            if volatility_score > 0.8:
                score -= 10
                signals.append("HIGH_VOLATILITY_FEAR")
            elif volatility_score < 0.2:
                score += 5
                signals.append("LOW_VOLATILITY_GREED")

        if funding_rate is not None:
            if funding_rate > 0.01:
                score += 10
                signals.append("HIGH_FUNDING_GREED")
            elif funding_rate < -0.01:
                score -= 10
                signals.append("NEGATIVE_FUNDING_FEAR")

        score = max(0, min(100, round(score)))

        if score >= 75:
            label = "EXTREME_GREED"
        elif score >= 55:
            label = "GREED"
        elif score >= 45:
            label = "NEUTRAL"
        elif score >= 25:
            label = "FEAR"
        else:
            label = "EXTREME_FEAR"

        return {
            "value": score,
            "label": label,
            "signals": signals,
            "confidence": round(1.0 - abs(score - 50) / 100, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
