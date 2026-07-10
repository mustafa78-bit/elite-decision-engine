"""Whale activity tracking — computed from market conditions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class WhaleService:
    """Detect whale activity signals from market data."""

    def detect(
        self,
        symbol: str,
        volume_score: Optional[float] = None,
        volatility_score: Optional[float] = None,
        price: float = 0.0,
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if volume_score is not None and volume_score > 0.9:
            signals.append({
                "type": "HIGH_VOLUME",
                "symbol": symbol,
                "severity": "high" if volume_score > 0.95 else "medium",
                "description": "Unusually high volume detected",
                "confidence": round(volume_score, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        if volume_score and volatility_score:
            combined = volume_score * volatility_score
            if combined > 0.7:
                signals.append({
                    "type": "WHALE_MOVE",
                    "symbol": symbol,
                    "severity": "high" if combined > 0.85 else "medium",
                    "description": "Potential whale accumulation/distribution",
                    "confidence": round(combined, 2),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        return signals
