"""ConfidenceEngineV2 — enhanced confidence using MIP intelligence."""

from __future__ import annotations

import logging
from typing import Any, Optional

from market.models import Asset
from scanner.models import Opportunity

logger = logging.getLogger(__name__)


class ConfidenceEngineV2:
    """Enhanced confidence calculation using full Asset intelligence."""

    def evaluate_opportunity(self, opportunity: Opportunity, asset: Optional[Asset] = None) -> float:
        base = opportunity.score * 100
        adjustments: list[float] = []

        if opportunity.probability_score > 0:
            prob_weight = opportunity.probability_score / 100
            adjustments.append(prob_weight * 20 - 10)

        if opportunity.risk_score > 0:
            risk_penalty = (1.0 - opportunity.risk_score) * 15 - 7.5
            adjustments.append(risk_penalty)

        if opportunity.confidence > 0:
            adjustments.append((opportunity.confidence - 50) * 0.2)

        if asset and asset.intelligence:
            intel_conf = asset.intelligence.confidence
            adjustments.append(intel_conf * 10 - 5)

            fg = asset.intelligence.fear_greed
            if fg:
                fg_value = fg.get("value", 50)
                if fg_value < 20:
                    adjustments.append(8)
                elif fg_value > 80:
                    adjustments.append(-5)

        if asset:
            ctx = asset.context
            session = ctx.get("session", "")
            if session == "NY":
                adjustments.append(3)
            elif session in ("ASIAN",):
                adjustments.append(-2)

            btc = ctx.get("btc", {})
            btc_trend = btc.get("btc_trend", "")
            if btc_trend == "BULLISH":
                adjustments.append(5)
            elif btc_trend == "BEARISH":
                adjustments.append(-5)

        total = base + sum(adjustments)
        return round(max(0.0, min(100.0, total)), 2)

    def evaluate_asset(self, asset: Asset, side: str = "LONG") -> float:
        indicators = asset.indicators
        features = asset.features
        base = 50.0

        rsi = indicators.get("rsi", 50)
        if side == "LONG":
            if 40 <= rsi <= 60:
                base += 10
            elif rsi < 30:
                base += 15
            elif rsi > 70:
                base -= 10
        else:
            if 40 <= rsi <= 60:
                base += 10
            elif rsi > 70:
                base += 15
            elif rsi < 30:
                base -= 10

        trend = features.get("trend", "NEUTRAL")
        if side == "LONG" and trend in ("BULLISH", "MILD_BULLISH"):
            base += 15
        elif side == "SHORT" and trend in ("BEARISH", "MILD_BEARISH"):
            base += 15

        momentum = features.get("momentum", "NEUTRAL")
        if momentum in ("STRONG",):
            base += 10
        elif momentum in ("WEAK",):
            base -= 5

        risk = features.get("risk", "MEDIUM")
        if risk == "LOW":
            base += 5
        elif risk == "HIGH":
            base -= 10

        if asset.intelligence:
            base += asset.intelligence.confidence * 10

        return round(max(0.0, min(100.0, base)), 2)
