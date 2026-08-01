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
from scoring.regime_ai import RegimeAI

logger = logging.getLogger(__name__)

DIRECTION_MAP: dict[str, str] = {
    "TREND": DIRECTION_BULLISH,
    "DOWNTREND": DIRECTION_BEARISH,
    "RECOVERY": DIRECTION_BULLISH,
    "RANGE": DIRECTION_NEUTRAL,
    "DEAD": DIRECTION_PASS,
    "UNKNOWN": DIRECTION_NEUTRAL,
}

TREND_MAP: dict[str, str] = {
    "BULLISH": DIRECTION_BULLISH,
    "BEARISH": DIRECTION_BEARISH,
    "RECOVERING": DIRECTION_BULLISH,
    "WEAKENING": DIRECTION_BEARISH,
    "NEUTRAL": DIRECTION_NEUTRAL,
}


class TrendAgent(BaseAgent):
    """Evaluates market regime and trend direction.

    Wraps RegimeAI to assess the broader market trend, regime class,
    trend strength, and market phase for a given symbol.
    """

    def __init__(
        self,
        name: str = "Trend",
        weight: float = 1.0,
        priority: int = 5,
        regime_ai: Optional[RegimeAI] = None,
    ) -> None:
        super().__init__(name=name, weight=weight, priority=priority)
        self.regime_ai = regime_ai or RegimeAI()

    def evaluate(
        self,
        signal: Optional[TradingSignal] = None,
        scores: Optional[dict[str, Any]] = None,
        market_data: Optional[Any] = None,
        **kwargs: Any,
    ) -> AgentReport:
        symbol = getattr(signal, "symbol", "?") if signal else "?"
        side = getattr(signal, "side", "LONG") if signal else "LONG"

        values: Optional[dict[str, Any]] = None
        if scores:
            values = {
                "ema20": scores.get("ema20"),
                "ema50": scores.get("ema50"),
                "ema200": scores.get("ema200"),
                "atr": scores.get("atr"),
                "close": scores.get("entry"),
                "rsi": scores.get("rsi"),
            }

        if kwargs.get("regime_context"):
            raw = kwargs["regime_context"]
        else:
            raw = self.regime_ai.detect(values)

        regime = raw.get("regime", "UNKNOWN")
        trend = raw.get("trend", "NEUTRAL")
        trend_strength = raw.get("trend_strength", "UNKNOWN")
        volatility_class = raw.get("volatility_class", "UNKNOWN")
        market_phase = raw.get("market_phase", "UNKNOWN")
        regime_score = raw.get("score", 0.0)

        direction = DIRECTION_MAP.get(regime, DIRECTION_NEUTRAL)
        if direction == DIRECTION_NEUTRAL:
            direction = TREND_MAP.get(trend, DIRECTION_NEUTRAL)

        reasoning: list[str] = []
        if regime != "UNKNOWN":
            reasoning.append(f"Regime: {regime}")
        if trend != "NEUTRAL":
            reasoning.append(f"Trend: {trend} ({trend_strength})")
        if market_phase != "UNKNOWN":
            reasoning.append(f"Market phase: {market_phase}")
        if volatility_class != "UNKNOWN":
            reasoning.append(f"Volatility: {volatility_class}")

        direction_score = 0.5
        if regime == "TREND":
            direction_score = 0.9
        elif regime == "RECOVERY":
            direction_score = 0.7
        elif regime == "RANGE":
            direction_score = 0.5
        elif regime == "DOWNTREND":
            direction_score = 0.3
        elif regime == "DEAD":
            direction_score = 0.1

        if trend_strength == "STRONG":
            direction_score = min(1.0, direction_score + 0.1)
        elif trend_strength == "WEAK":
            direction_score = max(0.0, direction_score - 0.1)

        if direction == DIRECTION_PASS and regime_score < 0.3:
            reasoning.append("Market too quiet — no trend signal")

        return AgentReport(
            agent_name=self.name,
            symbol=symbol,
            direction=direction,
            confidence=round(direction_score, 4),
            score=round(regime_score, 4),
            reasoning=reasoning,
            data_points={
                "regime": regime,
                "trend": trend,
                "trend_strength": trend_strength,
                "volatility_class": volatility_class,
                "market_phase": market_phase,
                "regime_score": regime_score,
            },
        )
