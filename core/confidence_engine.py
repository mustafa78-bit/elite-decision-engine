class ConfidenceEngine:
    """
    Final decision engine.

    Converts individual component scores into a
    single confidence score (0-100).
    """

    def calculate(self, score):

        confidence = (
            score["trend_score"] * 30 +
            score["volume_score"] * 20 +
            score["btc_score"] * 20 +
            score["mtf_score"] * 20 +
            score["risk_score"] * 10
        )

        confidence = max(0, min(100, confidence * 100))

        if confidence >= 90:
            decision = "STRONG_APPROVE"
        elif confidence >= 80:
            decision = "APPROVE"
        elif confidence >= 70:
            decision = "WATCH"
        else:
            decision = "REJECT"

        return {
            "confidence": round(confidence, 2),
            "decision": decision,
        }
