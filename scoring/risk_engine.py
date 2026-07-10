import logging
from typing import Any

logger = logging.getLogger(__name__)


class RiskEngine:

    def evaluate(self, values, volatility) -> dict[str, Any]:
        atr = values.get("atr", 0)
        risk_score = 1.0

        penalties: dict[str, float] = {}

        vol_score = volatility.get("score", 0)
        vol_penalty = vol_score * 0.60
        if vol_penalty > 0:
            risk_score -= vol_penalty
            penalties["volatility"] = round(vol_penalty, 4)

        if atr > 0:
            if atr > 2500:
                risk_score -= 0.20
                penalties["atr_extreme"] = 0.20
            elif atr > 1500:
                risk_score -= 0.10
                penalties["atr_high"] = 0.10
            elif atr > 700:
                risk_score -= 0.05
                penalties["atr_moderate"] = 0.05

        risk_score = max(0.0, min(1.0, risk_score))

        logger.debug(
            "RiskEngine.evaluate: atr=%s vol_score=%s penalties=%s result=%s",
            atr, vol_score, penalties, risk_score,
        )

        return {
            "risk_score": round(risk_score, 2),
            "penalties": penalties,
            "atr": atr,
            "volatility_score": vol_score,
        }

    def score(self, values, volatility) -> float:
        return self.evaluate(values, volatility)["risk_score"]
