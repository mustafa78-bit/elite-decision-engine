"""Convert raw indicators into categorical AI features.

Examples:
  Trend = BULLISH / BEARISH / NEUTRAL
  Momentum = STRONG / MODERATE / WEAK
  Risk = LOW / MEDIUM / HIGH
  Liquidity = HIGH / MEDIUM / LOW
  Volatility = LOW / NORMAL / HIGH / EXTREME
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FeatureStore:
    """Translate numeric indicators into human-readable categorical features."""

    def extract(self, indicators: dict[str, Any], side: str = "LONG") -> dict[str, Any]:
        if not indicators:
            return {
                "trend": "UNKNOWN",
                "momentum": "UNKNOWN",
                "risk": "UNKNOWN",
                "liquidity": "UNKNOWN",
                "volatility_class": "UNKNOWN",
                "regime_score": 0.0,
            }

        ema20 = indicators.get("ema20", 0)
        ema50 = indicators.get("ema50", 0)
        ema200 = indicators.get("ema200", 0)
        rsi = indicators.get("rsi", 50)
        atr = indicators.get("atr", 0)
        vol_score = indicators.get("volatility_score", 0)
        volume_score = indicators.get("volume_score", 0)

        trend = self._classify_trend(ema20, ema50, ema200, side)
        momentum = self._classify_momentum(rsi)
        risk = self._classify_risk(vol_score, atr)
        liquidity = self._classify_liquidity(volume_score)
        vol_class = self._classify_volatility(atr, indicators.get("entry", ema20))

        return {
            "trend": trend,
            "momentum": momentum,
            "risk": risk,
            "liquidity": liquidity,
            "volatility_class": vol_class,
            "regime_score": self._regime_score(trend, momentum, risk),
        }

    def _classify_trend(self, ema20: float, ema50: float, ema200: float, side: str) -> str:
        if ema20 <= 0 or ema50 <= 0:
            return "NEUTRAL"
        if side == "LONG":
            if ema20 > ema50 > ema200:
                return "BULLISH"
            if ema20 > ema50:
                return "MILD_BULLISH"
            if ema20 < ema50 < ema200:
                return "BEARISH"
            if ema50 > ema200:
                return "MILD_BEARISH"
            return "NEUTRAL"
        else:
            if ema20 < ema50 < ema200:
                return "BULLISH"
            if ema20 < ema50:
                return "MILD_BULLISH"
            if ema20 > ema50 > ema200:
                return "BEARISH"
            if ema50 < ema200:
                return "MILD_BEARISH"
            return "NEUTRAL"

    def _classify_momentum(self, rsi: float) -> str:
        if rsi >= 70:
            return "OVERBOUGHT"
        if rsi >= 55:
            return "STRONG"
        if rsi >= 45:
            return "NEUTRAL"
        if rsi >= 30:
            return "WEAK"
        return "OVERSOLD"

    def _classify_risk(self, vol_score: float, atr: float) -> str:
        risk_level = 0
        if vol_score > 0.7:
            risk_level += 2
        elif vol_score > 0.4:
            risk_level += 1
        if atr > 2500:
            risk_level += 2
        elif atr > 1500:
            risk_level += 1
        if risk_level >= 3:
            return "HIGH"
        if risk_level >= 1:
            return "MEDIUM"
        return "LOW"

    def _classify_liquidity(self, volume_score: float) -> str:
        if volume_score >= 0.8:
            return "HIGH"
        if volume_score >= 0.5:
            return "MEDIUM"
        if volume_score > 0:
            return "LOW"
        return "UNKNOWN"

    def _classify_volatility(self, atr: float, price: float) -> str:
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

    def _regime_score(self, trend: str, momentum: str, risk: str) -> float:
        score = 0.5
        if trend in ("BULLISH",):
            score += 0.2
        if momentum in ("STRONG",):
            score += 0.15
        if risk == "LOW":
            score += 0.15
        if trend in ("BEARISH",):
            score -= 0.2
        if risk == "HIGH":
            score -= 0.15
        if momentum in ("OVERBOUGHT", "OVERSOLD"):
            score -= 0.1
        return round(max(0.0, min(1.0, score)), 2)
