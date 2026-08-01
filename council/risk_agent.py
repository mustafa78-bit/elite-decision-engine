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
from scoring.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Evaluates trade risk: volatility, ATR, position risk.

    Wraps the RiskEngine and provides a risk-focused agent report.
    """

    def __init__(
        self,
        name: str = "Risk",
        weight: float = 1.0,
        priority: int = 5,
        risk_engine: Optional[RiskEngine] = None,
    ) -> None:
        super().__init__(name=name, weight=weight, priority=priority)
        self.risk_engine = risk_engine or RiskEngine()

    def evaluate(
        self,
        signal: Optional[TradingSignal] = None,
        scores: Optional[dict[str, Any]] = None,
        market_data: Optional[Any] = None,
        **kwargs: Any,
    ) -> AgentReport:
        symbol = getattr(signal, "symbol", "?") if signal else "?"

        if scores is None:
            return AgentReport(
                agent_name=self.name,
                symbol=symbol,
                direction=DIRECTION_NEUTRAL,
                confidence=0.5,
                score=0.5,
                reasoning=["No score data — defaulting to neutral risk"],
                data_points={},
            )

        values = {
            "atr": scores.get("atr", 0),
        }
        volatility = {
            "score": scores.get("risk_score", 0.5),
            "volatility": scores.get("volatility", 0),
        }

        try:
            risk_result = self.risk_engine.evaluate(values, volatility)
        except Exception as e:
            logger.warning("RiskAgent evaluation failed for %s: %s", symbol, e)
            return AgentReport(
                agent_name=self.name,
                symbol=symbol,
                direction=DIRECTION_PASS,
                confidence=0.0,
                score=0.0,
                reasoning=[f"Risk evaluation error: {e}"],
            )

        risk_score = risk_result.get("risk_score", 0.5)
        penalties = risk_result.get("penalties", {})
        atr = risk_result.get("atr", 0)
        vol_score = risk_result.get("volatility_score", 0)

        reasoning: list[str] = []
        direction = DIRECTION_NEUTRAL
        confidence = 0.5

        if risk_score >= 0.8:
            direction = DIRECTION_BULLISH
            confidence = risk_score
            reasoning.append("Low risk environment — favourable for trading")
        elif risk_score >= 0.6:
            direction = DIRECTION_NEUTRAL
            confidence = risk_score
            reasoning.append("Moderate risk — proceed with caution")
        elif risk_score >= 0.4:
            direction = DIRECTION_BEARISH
            confidence = risk_score
            reasoning.append("Elevated risk — reduce position size")
        else:
            direction = DIRECTION_PASS
            confidence = risk_score
            reasoning.append("High risk — avoid trading")

        if "volatility" in penalties:
            reasoning.append(f"Volatility penalty: {penalties['volatility']:.2f}")
        if "atr_extreme" in penalties:
            reasoning.append("ATR extreme — very wide stops")
        elif "atr_high" in penalties:
            reasoning.append("ATR high — wide stops required")
        elif "atr_moderate" in penalties:
            reasoning.append("ATR moderate — normal stop distance")

        return AgentReport(
            agent_name=self.name,
            symbol=symbol,
            direction=direction,
            confidence=round(confidence, 4),
            score=round(risk_score, 4),
            reasoning=reasoning,
            data_points={
                "risk_score": risk_score,
                "atr": atr,
                "volatility_score": vol_score,
                "penalties": penalties,
            },
        )
