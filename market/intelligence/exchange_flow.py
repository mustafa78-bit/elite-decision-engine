"""Exchange flow analysis — heuristic proxy, not real on-chain data."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ExchangeFlowService:
    """Analyze exchange flow patterns from market data."""

    def analyze(
        self,
        symbol: str,
        volume_score: float | None = None,
        volatility_score: float | None = None,
        trend: str | None = None,
    ) -> dict[str, Any]:
        net_flow = 0.0
        signals: list[str] = []

        if volume_score is not None:
            if volume_score > 0.8:
                net_flow -= 0.3
                signals.append("HIGH_OUTFLOW_VOLUME")
            elif volume_score > 0.5:
                net_flow -= 0.1
                signals.append("MODERATE_OUTFLOW")
            else:
                net_flow += 0.1
                signals.append("LOW_INFLOW")

        if volatility_score is not None:
            if volatility_score > 0.7 and trend == "BULLISH":
                net_flow += 0.2
                signals.append("VOLATILE_BULLISH_INFLOW")
            elif volatility_score > 0.7 and trend == "BEARISH":
                net_flow -= 0.2
                signals.append("VOLATILE_BEARISH_OUTFLOW")

        flow_direction = "NET_INFLOW" if net_flow > 0 else "NET_OUTFLOW" if net_flow < 0 else "NEUTRAL"

        return {
            "symbol": symbol,
            "net_flow": round(net_flow, 4),
            "direction": flow_direction,
            "signals": signals,
            "confidence": round(abs(net_flow), 2),
            "timestamp": datetime.now(UTC).isoformat(),
        }
