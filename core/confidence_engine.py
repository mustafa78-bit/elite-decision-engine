import logging

from config import SCORE_WEIGHTS_PCT

logger = logging.getLogger(__name__)


class ConfidenceEngine:
    """
    Final decision engine.

    Converts individual component scores into a
    single confidence score (0-100).
    """

    def calculate(self, score):

        trend = (score.get("trend_score") or 0) * SCORE_WEIGHTS_PCT["trend"]
        volume = (score.get("volume_score") or 0) * SCORE_WEIGHTS_PCT["volume"]
        btc = (score.get("btc_score") or 0) * SCORE_WEIGHTS_PCT["btc"]
        mtf = (score.get("mtf_score") or 0) * SCORE_WEIGHTS_PCT["mtf"]
        risk = (score.get("risk_score") or 0) * SCORE_WEIGHTS_PCT["risk"]

        confidence = trend + volume + btc + mtf + risk
        confidence = max(0, min(100, confidence))

        if confidence >= 90:
            decision = "STRONG_APPROVE"
        elif confidence >= 80:
            decision = "APPROVE"
        elif confidence >= 70:
            decision = "WATCH"
        else:
            decision = "REJECT"

        logger.debug(
            "Confidence: trend=%.1f vol=%.1f btc=%.1f mtf=%.1f risk=%.1f total=%.1f decision=%s",
            trend, volume, btc, mtf, risk, confidence, decision,
        )

        return {
            "confidence": round(confidence, 2),
            "decision": decision,
        }
