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
        imbalance: Optional[float] = None,
        latest_rate: Optional[float] = None,
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

        if imbalance is not None:
            wall_type = "Support" if imbalance > 0 else "Resistance"
            confidence = round(abs(imbalance), 2)
            # High severity for high magnitude imbalances (e.g. abs(imbalance) >= 0.8)
            severity = "high" if confidence >= 0.8 else "medium"
            signals.append({
                "type": "WHALE_WALL",
                "symbol": symbol,
                "wall_type": wall_type,
                "severity": severity,
                "description": f"Heavy {wall_type.lower()}-side order-book wall detected",
                "confidence": confidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        if latest_rate is not None:
            direction = "premium" if latest_rate > 0 else "discount"
            # Calculate confidence based on magnitude
            abs_rate = abs(latest_rate)
            if abs_rate > 0.01:
                # Annualized or percentage representation
                conf = min(1.0, abs_rate / 50.0)
            else:
                # Raw decimal funding rate representation
                conf = min(1.0, abs_rate * 500.0)
            conf = max(0.5, round(conf, 2))
            severity = "high" if conf >= 0.8 else "medium"
            signals.append({
                "type": "EXTREME_FUNDING",
                "symbol": symbol,
                "direction": direction,
                "severity": severity,
                "description": f"Extreme funding {direction} detected",
                "confidence": conf,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return signals
