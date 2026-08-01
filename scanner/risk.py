"""RiskScorer — risk assessment per opportunity."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RiskScorer:
    """Score risk level for a given opportunity."""

    def score(
        self,
        volatility_class: Optional[str] = None,
        risk_feature: Optional[str] = None,
        atr_pct: Optional[float] = None,
        liquidity_score: float = 0.0,
        reversal_score: float = 0.0,
    ) -> tuple[float, list[str]]:
        risk = 0.0
        signals: list[str] = []

        if volatility_class == "EXTREME":
            risk += 0.35
            signals.append("EXTREME_VOLATILITY_RISK")
        elif volatility_class == "HIGH":
            risk += 0.25
            signals.append("HIGH_VOLATILITY_RISK")
        elif volatility_class == "LOW":
            risk -= 0.1
            signals.append("LOW_VOLATILITY_BOOST")

        if risk_feature == "HIGH":
            risk += 0.3
            signals.append("HIGH_FEATURE_RISK")
        elif risk_feature == "MEDIUM":
            risk += 0.15
            signals.append("MEDIUM_FEATURE_RISK")
        elif risk_feature == "LOW":
            risk -= 0.1
            signals.append("LOW_FEATURE_RISK")

        if atr_pct is not None:
            if atr_pct > 5:
                risk += 0.3
                signals.append("HIGH_ATR_RISK")
            elif atr_pct > 2.5:
                risk += 0.15
                signals.append("MODERATE_ATR_RISK")

        if liquidity_score < 0.3:
            risk += 0.2
            signals.append("LOW_LIQUIDITY_RISK")
        elif liquidity_score > 0.7:
            risk -= 0.1
            signals.append("HIGH_LIQUIDITY_BOOST")

        if reversal_score > 0.5:
            risk += 0.1
            signals.append("REVERSAL_RISK")

        risk = round(max(0.0, min(1.0, risk)), 4)
        return risk, signals
