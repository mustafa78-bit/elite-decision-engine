from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RegimeAI:
    """Improved market regime detector with trend strength, volatility class, and market phase."""

    def detect(self, values: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Detect market regime with enhanced classification."""
        if values is None or not values:
            return {
                "regime": "UNKNOWN",
                "trend": "NEUTRAL",
                "trend_strength": "UNKNOWN",
                "volatility_class": "UNKNOWN",
                "market_phase": "UNKNOWN",
                "score": 0.0,
            }

        ema20 = float(values.get("ema20", 0))
        ema50 = float(values.get("ema50", 0))
        ema200 = float(values.get("ema200", 0))
        atr = float(values.get("atr", 0))
        price = float(values.get("close", 0))
        rsi = float(values.get("rsi", 50))

        regime = self._classify_regime(ema20, ema50, ema200, atr)
        trend = self._classify_trend(ema20, ema50, ema200)
        trend_strength = self._trend_strength(ema20, ema50, price)
        vol_class = self._volatility_class(atr, price)
        phase = self._market_phase(trend, trend_strength, rsi, price, ema200)

        return {
            "regime": regime,
            "trend": trend,
            "trend_strength": trend_strength,
            "volatility_class": vol_class,
            "market_phase": phase,
            "score": self._score(regime, trend_strength, vol_class),
        }

    def _classify_regime(self, ema20: float, ema50: float, ema200: float, atr: float) -> str:
        if atr < 100:
            return "DEAD"
        if ema20 > ema50 > ema200:
            return "TREND"
        if ema20 < ema50 < ema200:
            return "DOWNTREND"
        if ema20 > ema200 > ema50 or ema50 > ema200 > ema20:
            return "RECOVERY"
        return "RANGE"

    def _classify_trend(self, ema20: float, ema50: float, ema200: float) -> str:
        if ema20 > ema50 > ema200:
            return "BULLISH"
        if ema20 < ema50 < ema200:
            return "BEARISH"
        if ema20 > ema50 and ema50 < ema200:
            return "RECOVERING"
        if ema20 < ema50 and ema50 > ema200:
            return "WEAKENING"
        return "NEUTRAL"

    def _trend_strength(self, ema20: float, ema50: float, price: float) -> str:
        if ema20 <= 0 or ema50 <= 0 or price <= 0:
            return "UNKNOWN"
        slope_pct = abs(ema20 - ema50) / ema50 * 100
        price_slope_pct = abs(price - ema20) / ema20 * 100
        combined = slope_pct + price_slope_pct
        if combined > 5:
            return "STRONG"
        if combined > 2:
            return "MODERATE"
        return "WEAK"

    def _volatility_class(self, atr: float, price: float) -> str:
        if price <= 0 or atr <= 0:
            return "UNKNOWN"
        atr_pct = (atr / price) * 100
        if atr_pct > 5:
            return "EXTREME"
        if atr_pct > 2.5:
            return "HIGH"
        if atr_pct > 1.0:
            return "NORMAL"
        return "LOW"

    def _market_phase(self, trend: str, strength: str, rsi: float, price: float, ema200: float) -> str:
        if ema200 <= 0:
            return "UNKNOWN"
        above_200 = price > ema200

        if trend == "BULLISH" and strength == "STRONG" and rsi > 70:
            return "MARKUP"
        if trend == "BULLISH" and rsi < 40:
            return "ACCUMULATION"
        if trend == "BEARISH" and strength == "STRONG" and rsi < 30:
            return "MARKDOWN"
        if trend == "BEARISH" and above_200:
            return "DISTRIBUTION"
        if trend == "RECOVERING":
            return "ACCUMULATION"
        if trend == "WEAKENING":
            return "DISTRIBUTION"
        return "NEUTRAL"

    def _score(self, regime: str, trend_strength: str, vol_class: str) -> float:
        score = 0.6
        if regime in ("TREND", "RECOVERY"):
            score += 0.2
        if regime in ("DEAD", "DOWNTREND"):
            score -= 0.2
        if trend_strength == "STRONG":
            score += 0.1
        if vol_class == "EXTREME":
            score -= 0.2
        elif vol_class == "HIGH":
            score -= 0.1
        elif vol_class == "LOW":
            score += 0.1
        return round(max(0.0, min(1.0, score)), 2)
