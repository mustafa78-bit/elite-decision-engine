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
from config import SCORE_WEIGHTS
from execution.pipeline import TradingSignal
from scoring.scoring_engine import ScoringEngine

# TechnicalAgent deliberately excludes the "risk" term from SCORE_WEIGHTS --
# RiskAgent covers that separately in the council -- but the remaining 4
# weights (trend/volume/btc/mtf) only sum to 0.9, not 1.0, so a maximal
# reading across all four could never actually reach a composite of 1.0.
# Renormalizing by the weight actually in use here preserves the exact same
# relative proportions between the 4 terms while restoring a real 0-1 range.
_TECHNICAL_WEIGHT_SUM = (
    SCORE_WEIGHTS["trend"] + SCORE_WEIGHTS["volume"] + SCORE_WEIGHTS["btc"] + SCORE_WEIGHTS["mtf"]
)

logger = logging.getLogger(__name__)


class TechnicalAgent(BaseAgent):
    """Evaluates technical indicators: trend, volume, BTC health, MTF.

    Wraps the existing ScoringEngine to produce a dedicated agent report
    focused on technical analysis signals.
    """

    def __init__(
        self,
        name: str = "Technical",
        weight: float = 1.0,
        priority: int = 5,
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, priority=priority)
        self.scoring_engine = scoring_engine or ScoringEngine()

    def evaluate(
        self,
        signal: TradingSignal | None = None,
        scores: dict[str, Any] | None = None,
        market_data: Any | None = None,
        **kwargs: Any,
    ) -> AgentReport:
        symbol = getattr(signal, "symbol", "?") if signal else "?"
        side = getattr(signal, "side", "LONG") if signal else "LONG"

        if scores is None and signal is not None:
            try:
                scores = self.scoring_engine.score(signal)
            except Exception as e:
                logger.warning("TechnicalAgent scoring failed for %s: %s", symbol, e)
                return AgentReport(
                    agent_name=self.name,
                    symbol=symbol,
                    direction=DIRECTION_PASS,
                    confidence=0.0,
                    score=0.0,
                    reasoning=[f"Scoring failed: {e}"],
                )

        if scores is None:
            return AgentReport(
                agent_name=self.name,
                symbol=symbol,
                direction=DIRECTION_NEUTRAL,
                confidence=0.0,
                score=0.0,
                reasoning=["No scores available"],
            )

        trend_score = scores.get("trend_score", 0)
        volume_score = scores.get("volume_score", 0)
        btc_score = scores.get("btc_score", 0)
        mtf_score = scores.get("mtf_score", 0)
        final_score = scores.get("final_score", 0)

        contributions = scores.get("contributions", {})
        rsi = scores.get("rsi", 50)
        ema20 = scores.get("ema20", 0)
        ema50 = scores.get("ema50", 0)
        ema200 = scores.get("ema200", 0)

        composite = (
            trend_score * SCORE_WEIGHTS["trend"]
            + volume_score * SCORE_WEIGHTS["volume"]
            + btc_score * SCORE_WEIGHTS["btc"]
            + mtf_score * SCORE_WEIGHTS["mtf"]
        ) / _TECHNICAL_WEIGHT_SUM

        reasoning: list[str] = []
        direction = DIRECTION_NEUTRAL
        confidence = 0.5

        # Compute literal market direction (ignoring trade side)
        if ema20 > ema50 > ema200:
            direction = DIRECTION_BULLISH
            reasoning.append("Bullish EMA alignment (20 > 50 > 200)")
        elif ema20 < ema50 < ema200:
            direction = DIRECTION_BEARISH
            reasoning.append("Bearish EMA alignment (20 < 50 < 200)")
        elif ema20 > ema50 and ema50 < ema200:
            direction = DIRECTION_NEUTRAL
            reasoning.append("Mixed EMA signals — short-term bullish, long-term bearish")
        elif ema20 < ema50 and ema50 > ema200:
            direction = DIRECTION_NEUTRAL
            reasoning.append("Mixed EMA signals — short-term bearish, long-term bullish")
        elif ema20 < ema50:
            direction = DIRECTION_BEARISH
            reasoning.append("Bearish EMA cross (20 below 50)")
        elif ema20 > ema50:
            direction = DIRECTION_BULLISH
            reasoning.append("Bullish EMA cross (20 above 50)")
        else:
            direction = DIRECTION_NEUTRAL
            reasoning.append("Flat EMA structure")

        # Now normalize relative to the trade side
        direction = normalize_direction(direction, side)

        if rsi > 70:
            reasoning.append(f"RSI overbought ({rsi:.0f})")
        elif rsi < 30:
            reasoning.append(f"RSI oversold ({rsi:.0f})")

        if volume_score > 0.7:
            reasoning.append("High volume confirmation")
        elif volume_score < 0.3:
            reasoning.append("Low volume — weak conviction")

        if btc_score > 0.7:
            reasoning.append("BTC health favourable")
        elif btc_score < 0.3:
            reasoning.append("BTC health unfavourable")

        confidence = min(1.0, max(0.0, composite))
        score = min(1.0, max(0.0, final_score))

        if direction == DIRECTION_NEUTRAL and confidence < 0.4:
            direction = DIRECTION_PASS

        return AgentReport(
            agent_name=self.name,
            symbol=symbol,
            direction=direction,
            confidence=round(confidence, 4),
            score=round(score, 4),
            reasoning=reasoning,
            data_points={
                "trend_score": trend_score,
                "volume_score": volume_score,
                "btc_score": btc_score,
                "mtf_score": mtf_score,
                "final_score": final_score,
                "rsi": rsi,
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "contributions": contributions,
            },
        )
