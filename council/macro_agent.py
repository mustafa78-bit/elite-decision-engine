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

logger = logging.getLogger(__name__)

FUNDING_RISK_MAP: dict[str, float] = {
    "VERY_HIGH": 0.1,
    "HIGH": 0.3,
    "MODERATE": 0.5,
    "LOW": 0.7,
    "NEUTRAL": 0.5,
}

FEAR_GREED_MAP: dict[str, float] = {
    "EXTREME_FEAR": 0.2,
    "FEAR": 0.35,
    "NEUTRAL": 0.5,
    "GREED": 0.65,
    "EXTREME_GREED": 0.8,
}

OI_TREND_MAP: dict[str, str] = {
    "RISING": DIRECTION_BULLISH,
    "FALLING": DIRECTION_BEARISH,
    "FLAT": DIRECTION_NEUTRAL,
}


class MacroAgent(BaseAgent):
    """Evaluates macro market conditions: funding, open interest,
    fear & greed, liquidity, exchange flows.

    Uses the IntelligenceBundle produced by the IntelligenceService.
    """

    def __init__(
        self,
        name: str = "Macro",
        weight: float = 1.0,
        priority: int = 4,
    ) -> None:
        super().__init__(name=name, weight=weight, priority=priority)

    def evaluate(
        self,
        signal: Optional[TradingSignal] = None,
        scores: Optional[dict[str, Any]] = None,
        market_data: Optional[Any] = None,
        **kwargs: Any,
    ) -> AgentReport:
        symbol = getattr(signal, "symbol", "?") if signal else "?"
        side = getattr(signal, "side", "LONG") if signal else "LONG"

        bundle = kwargs.get("intelligence_bundle")

        if bundle is None:
            return AgentReport(
                agent_name=self.name,
                symbol=symbol,
                direction=DIRECTION_NEUTRAL,
                confidence=0.5,
                score=0.5,
                reasoning=["No intelligence bundle available"],
                data_points={},
            )

        funding = bundle.funding or {}
        open_interest = bundle.open_interest or {}
        fear_greed = bundle.fear_greed or {}
        liquidity = bundle.liquidity_context or {}
        exchange_flow = bundle.exchange_flow or {}

        funding_rate = funding.get("annualized_rate", 0)
        funding_level = funding.get("level", "NEUTRAL")
        funding_risk = funding.get("risk_score", 0.5)

        oi_value = open_interest.get("value", 0)
        oi_trend_name = open_interest.get("trend", "FLAT")
        oi_strength = open_interest.get("strength", 0.5)

        fg_label = fear_greed.get("label", "NEUTRAL")
        fg_value = fear_greed.get("value", 50)
        fg_confidence = fear_greed.get("confidence", 0.5)

        liq_score = liquidity.get("score", 0.5)
        liq_level = liquidity.get("level", "NEUTRAL")

        flow_direction = exchange_flow.get("direction", "NEUTRAL")
        flow_confidence = exchange_flow.get("confidence", 0.5)

        reasoning: list[str] = []
        scores_list: list[float] = []
        bullish_count = 0
        bearish_count = 0

        funding_score = FUNDING_RISK_MAP.get(funding_level, 0.5)
        scores_list.append(funding_score)
        if funding_rate != 0:
            reasoning.append(
                f"Funding rate: {funding_rate:+.6f} ({funding_level})"
            )
            if funding_level in ("HIGH", "VERY_HIGH"):
                bearish_count += 1
                reasoning.append("Elevated funding — crowded long")
            elif funding_level in ("LOW",):
                bullish_count += 1
                reasoning.append("Low funding — favourable")

        if oi_value > 0:
            oi_dir = OI_TREND_MAP.get(oi_trend_name, DIRECTION_NEUTRAL)
            scores_list.append(oi_strength)
            reasoning.append(
                f"OI trend: {oi_trend_name} (strength={oi_strength:.2f})"
            )
            if oi_dir == DIRECTION_BULLISH:
                bullish_count += 1
            elif oi_dir == DIRECTION_BEARISH:
                bearish_count += 1

        fg_score = FEAR_GREED_MAP.get(fg_label, 0.5)
        scores_list.append(fg_score)
        reasoning.append(f"Fear & Greed: {fg_label} ({fg_value})")
        if fg_label in ("EXTREME_FEAR", "FEAR"):
            bullish_count += 1
            reasoning.append("Fear — potential buying opportunity")
        elif fg_label in ("EXTREME_GREED", "GREED"):
            bearish_count += 1
            reasoning.append("Greed — market may be overextended")

        scores_list.append(liq_score)
        reasoning.append(f"Liquidity: {liq_level} (score={liq_score:.2f})")
        if liq_level == "HIGH":
            bullish_count += 1
        elif liq_level == "LOW":
            bearish_count += 1

        if exchange_flow:
            scores_list.append(flow_confidence)
            reasoning.append(f"Exchange flow: {flow_direction}")
            if flow_direction == "INFLOW":
                bearish_count += 1
                reasoning.append("Exchange inflow — potential selling pressure")
            elif flow_direction == "OUTFLOW":
                bullish_count += 1
                reasoning.append("Exchange outflow — accumulation signal")

        composite_score = sum(scores_list) / len(scores_list) if scores_list else 0.5

        direction = DIRECTION_NEUTRAL
        if bullish_count > bearish_count:
            direction = DIRECTION_BULLISH
        elif bearish_count > bullish_count:
            direction = DIRECTION_BEARISH

        return AgentReport(
            agent_name=self.name,
            symbol=symbol,
            direction=direction,
            confidence=round(composite_score, 4),
            score=round(composite_score, 4),
            reasoning=reasoning,
            data_points={
                "funding": funding,
                "open_interest": open_interest,
                "fear_greed": fear_greed,
                "liquidity": liquidity,
                "exchange_flow": exchange_flow,
                "bullish_signals": bullish_count,
                "bearish_signals": bearish_count,
                "composite_score": composite_score,
            },
        )
