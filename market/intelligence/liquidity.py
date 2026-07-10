"""Enhanced liquidity context analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LiquidityContextAnalyzer:
    """Provide enhanced liquidity context beyond basic classification."""

    def analyze(
        self,
        symbol: str,
        volume_score: Optional[float] = None,
        liquidity: Optional[str] = None,
        atr: Optional[float] = None,
        price: float = 0.0,
    ) -> dict[str, Any]:
        liquidity_score = 0.5
        signals: list[str] = []

        if liquidity == "HIGH":
            liquidity_score = 0.8
            signals.append("HIGH_LIQUIDITY")
        elif liquidity == "MEDIUM":
            liquidity_score = 0.5
            signals.append("MEDIUM_LIQUIDITY")
        elif liquidity == "LOW":
            liquidity_score = 0.2
            signals.append("LOW_LIQUIDITY_WARNING")

        if volume_score is not None:
            liquidity_score = (liquidity_score + volume_score) / 2
            if volume_score > 0.8:
                signals.append("STRONG_VOLUME_DEPTH")
            elif volume_score < 0.3:
                signals.append("WEAK_VOLUME_WARNING")

        if atr and price > 0:
            atr_pct = atr / price * 100
            if atr_pct > 5:
                liquidity_score *= 0.7
                signals.append("HIGH_SPREAD_WARNING")
            elif atr_pct > 2:
                liquidity_score *= 0.9
                signals.append("MODERATE_SPREAD")

        liquidity_score = round(max(0.0, min(1.0, liquidity_score)), 4)

        if liquidity_score >= 0.7:
            level = "HIGH"
        elif liquidity_score >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "symbol": symbol,
            "score": liquidity_score,
            "level": level,
            "signals": signals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
