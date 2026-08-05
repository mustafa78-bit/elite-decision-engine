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
    normalize_direction,
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
        whale_service: WhaleService | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, priority=priority)
        self.whale_service = whale_service or WhaleService()

    def evaluate(
        self,
        signal: TradingSignal | None = None,
        scores: dict[str, Any] | None = None,
        market_data: Any | None = None,
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
        confidence = min(1.0, max_confidence)

        types = [s.get("type", "UNKNOWN") for s in whale_signals]
        for signal_type in set(types):
            count = types.count(signal_type)
            reasoning.append(f"{count}x {signal_type} signal(s)")

        has_directional = any(t in {"WHALE_WALL", "EXTREME_FUNDING"} for t in types)

        if has_directional:
            # Weighted consensus across directional signal types. direction_val
            # is always the LITERAL market direction (+1 bullish, -1 bearish) --
            # normalize_direction() below converts it relative to trade side, the
            # same convention every other council agent follows.
            total_influence = 0.0
            for s in whale_signals:
                s_type = s.get("type")
                s_conf = s.get("confidence", 0.5)
                s_sev = s.get("severity", "medium")

                if s_sev == "high":
                    s_weight = 2.0
                elif s_sev == "medium":
                    s_weight = 1.0
                else:
                    s_weight = 0.5

                if s_type == "WHALE_WALL":
                    wall_type = s.get("wall_type")
                    direction_val = 1 if wall_type == "Support" else -1
                    reasoning.append(f"Whale wall: {wall_type} (conf={s_conf})")
                elif s_type == "EXTREME_FUNDING":
                    fund_dir = s.get("direction")
                    direction_val = 1 if fund_dir == "premium" else -1
                    reasoning.append(f"Extreme funding: {fund_dir} (conf={s_conf})")
                elif s_type == "WHALE_MOVE":
                    direction_val = 1
                    reasoning.append("Whale movement detected")
                else:
                    direction_val = 0
                    if s_type == "HIGH_VOLUME":
                        reasoning.append("Unusually high volume")

                total_influence += direction_val * s_weight * s_conf

            if total_influence > 0.05:
                literal_direction = DIRECTION_BULLISH
            elif total_influence < -0.05:
                literal_direction = DIRECTION_BEARISH
            else:
                literal_direction = DIRECTION_NEUTRAL
        else:
            # Legacy non-directional fallback: WHALE_MOVE/HIGH_VOLUME carry no
            # inherent market direction of their own, so a high-severity reading
            # is treated as a literal-bullish signal, same as before.
            literal_direction = DIRECTION_NEUTRAL
            if "WHALE_MOVE" in types:
                if high_severity:
                    literal_direction = DIRECTION_BULLISH
                    reasoning.append("High-confidence whale movement detected")
                else:
                    reasoning.append("Moderate whale movement — monitor closely")

            if "HIGH_VOLUME" in types:
                reasoning.append("Unusually high volume — possible institutional activity")

            if high_severity and confidence > 0.7:
                literal_direction = DIRECTION_BULLISH

        direction = normalize_direction(literal_direction, side)

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
