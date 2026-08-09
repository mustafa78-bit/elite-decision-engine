import logging
from typing import Any

logger = logging.getLogger(__name__)


class RiskEngine:

    def evaluate(self, values, volatility, price: float = 0.0) -> dict[str, Any]:
        atr = values.get("atr", 0)
        risk_score = 1.0

        penalties: dict[str, float] = {}

        vol_score = volatility.get("score", 0)
        vol_penalty = vol_score * 0.60
        if vol_penalty > 0:
            risk_score -= vol_penalty
            penalties["volatility"] = round(vol_penalty, 4)

        # ATR is a raw price-unit amount, not comparable across symbols at
        # different price scales without normalizing by price first (same
        # atr_pct pattern risk/execution_guard.py already uses).
        atr_pct = (atr / price) * 100 if price > 0 else 0
        if atr_pct > 0:
            if atr_pct > 10:
                risk_score -= 0.20
                penalties["atr_extreme"] = 0.20
            elif atr_pct > 6:
                risk_score -= 0.10
                penalties["atr_high"] = 0.10
            elif atr_pct > 3:
                risk_score -= 0.05
                penalties["atr_moderate"] = 0.05

        risk_score = max(0.0, min(1.0, risk_score))

        logger.debug(
            "RiskEngine.evaluate: atr=%s atr_pct=%.2f vol_score=%s penalties=%s result=%s",
            atr, atr_pct, vol_score, penalties, risk_score,
        )

        return {
            "risk_score": round(risk_score, 2),
            "penalties": penalties,
            "atr": atr,
            "atr_pct": round(atr_pct, 4),
            "volatility_score": vol_score,
        }

    def score(self, values, volatility, price: float = 0.0) -> float:
        return self.evaluate(values, volatility, price)["risk_score"]
