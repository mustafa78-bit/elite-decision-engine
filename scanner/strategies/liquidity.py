from __future__ import annotations

from typing import Any


class LiquidityStrategy:
    """Score liquidity conditions for safe execution."""

    name = "liquidity"

    def evaluate(self, asset: Any) -> tuple[float, list[str]]:
        features = asset.features
        indicators = asset.indicators
        signals: list[str] = []

        liquidity = features.get("liquidity", "UNKNOWN")
        volume_score = indicators.get("volume_score", 0)

        score = 0.0

        if liquidity == "HIGH":
            score += 0.6
            signals.append("HIGH_LIQUIDITY")
        elif liquidity == "MEDIUM":
            score += 0.3
            signals.append("MEDIUM_LIQUIDITY")
        elif liquidity == "LOW":
            score += 0.1
            signals.append("LOW_LIQUIDITY")

        if volume_score >= 0.8:
            score += 0.4
            signals.append("HIGH_VOLUME")
        elif volume_score >= 0.5:
            score += 0.2
            signals.append("MODERATE_VOLUME")

        return round(min(score, 1.0), 4), signals
