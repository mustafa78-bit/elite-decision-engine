"""ConfidenceScorer — overall confidence from probability, risk, and features."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Combine probability, risk, and intelligence confidence into a single score."""

    def compute(
        self,
        probability: float = 0.0,
        risk_score: float = 0.5,
        intelligence_confidence: float = 0.0,
        signal_count: int = 0,
    ) -> tuple[float, list[str]]:
        signals: list[str] = []

        if probability <= 0:
            return 0.0, ["NO_PROBABILITY"]

        base = probability

        risk_adjustment = (1.0 - risk_score) * 20
        base = base * (1.0 + (risk_adjustment - 10) / 100)

        if intelligence_confidence > 0:
            intel_boost = intelligence_confidence * 10
            base += intel_boost
            if intelligence_confidence > 0.7:
                signals.append("HIGH_INTELLIGENCE_BOOST")
            elif intelligence_confidence > 0.4:
                signals.append("MODERATE_INTELLIGENCE_BOOST")

        if signal_count >= 6:
            base += 5
            signals.append("MULTI_SIGNAL_CONFIRMATION")
        elif signal_count >= 3:
            base += 2
            signals.append("MODERATE_SIGNAL_CONFIRMATION")
        elif signal_count <= 1:
            base -= 5
            signals.append("LOW_SIGNAL_WARNING")

        confidence = max(0.0, min(100.0, round(base, 2)))
        return confidence, signals
