from __future__ import annotations

import logging
from typing import Any, Optional

from council.base import (
    DIRECTION_BEARISH,
    DIRECTION_BULLISH,
    DIRECTION_NEUTRAL,
    DIRECTION_PASS,
    AgentReport,
    BaseAgent,
)
from execution.pipeline import TradingSignal
from market.intelligence.whale import WhaleService

logger = logging.getLogger(__name__)


class WhaleAgent(BaseAgent):
    """Evaluates whale activity signals.

    Wraps WhaleService to detect large-volume moves suggesting
    institutional or whale accumulation/distribution.
    """

    def __init__(
        self,
        name: str = "Whale",
        weight: float = 1.0,
        priority: int = 3,
        whale_service: Optional[WhaleService] = None,
    ) -> None:
        super().__init__(name=name, weight=weight, priority=priority)
        self.whale_service = whale_service or WhaleService()

    def evaluate(
        self,
        signal: Optional[TradingSignal] = None,
        scores: Optional[dict[str, Any]] = None,
        market_data: Optional[Any] = None,
        **kwargs: Any,
    ) -> AgentReport:
        symbol = getattr(signal, "symbol", "?") if signal else "?"
        side = getattr(signal, "side", "LONG") if signal else "LONG"

        intelligence_bundle = kwargs.get("intelligence_bundle")

        whale_signals: list[dict[str, Any]] = []

        if intelligence_bundle is not None:
            whale_signals = getattr(intelligence_bundle, "whales", [])
        else:
            volume_score = scores.get("volume_score") if scores else None
            vol_score = scores.get("risk_score") if scores else None
            price = kwargs.get("price", 0.0)
            try:
                whale_signals = self.whale_service.detect(
                    symbol=symbol,
                    volume_score=volume_score,
                    volatility_score=vol_score,
                    price=price,
                )
            except Exception as e:
                logger.warning("WhaleAgent detection failed for %s: %s", symbol, e)
                return AgentReport(
                    agent_name=self.name,
                    symbol=symbol,
                    direction=DIRECTION_NEUTRAL,
                    confidence=0.0,
                    score=0.0,
                    reasoning=[f"Whale detection failed: {e}"],
                )

        if not whale_signals:
            return AgentReport(
                agent_name=self.name,
                symbol=symbol,
                direction=DIRECTION_NEUTRAL,
                confidence=0.0,
                score=0.5,
                reasoning=["No whale activity detected"],
                data_points={"signal_count": 0},
            )

        max_confidence = max(s.get("confidence", 0) for s in whale_signals)
        high_severity = any(s.get("severity") == "high" for s in whale_signals)

        reasoning: list[str] = []
        direction = DIRECTION_NEUTRAL
        confidence = min(1.0, max_confidence)

        types = [s.get("type", "UNKNOWN") for s in whale_signals]
        for signal_type in set(types):
            count = types.count(signal_type)
            reasoning.append(f"{count}x {signal_type} signal(s)")

        if "WHALE_MOVE" in types:
            if high_severity:
                direction = DIRECTION_BULLISH if side.upper() == "LONG" else DIRECTION_BEARISH
                reasoning.append("High-confidence whale movement detected")
            else:
                reasoning.append("Moderate whale movement — monitor closely")

        if "HIGH_VOLUME" in types:
            reasoning.append("Unusually high volume — possible institutional activity")

        if high_severity and confidence > 0.7:
            direction = DIRECTION_BULLISH if side.upper() == "LONG" else DIRECTION_BEARISH

        return AgentReport(
            agent_name=self.name,
            symbol=symbol,
            direction=direction,
            confidence=round(confidence, 4),
            score=round(max_confidence, 4),
            reasoning=reasoning,
            data_points={
                "signal_count": len(whale_signals),
                "max_confidence": max_confidence,
                "high_severity": high_severity,
                "signals": whale_signals,
            },
        )
