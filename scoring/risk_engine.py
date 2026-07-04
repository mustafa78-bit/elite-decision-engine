class RiskEngine:

    def score(self, values, volatility):

        atr = values.get("atr", 0)

        risk_score = 1.0

        # Volatility penalty
        risk_score -= volatility["score"] * 0.60

        # ATR penalty
        if atr > 0:
            if atr > 2500:
                risk_score -= 0.20
            elif atr > 1500:
                risk_score -= 0.10
            elif atr > 700:
                risk_score -= 0.05

        risk_score = max(0.0, min(1.0, risk_score))

        return round(risk_score, 2)
