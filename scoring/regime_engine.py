class RegimeEngine:

    def detect(self, values):

        ema20 = values.get("ema20", 0)
        ema50 = values.get("ema50", 0)
        ema200 = values.get("ema200", 0)
        atr = values.get("atr", 0)

        # Dead market
        if atr < 150:
            return {
                "regime": "DEAD",
                "score": 0.20
            }

        # Strong trend
        if ema20 > ema50 > ema200:
            return {
                "regime": "TREND",
                "score": 1.00
            }

        # Down trend
        if ema20 < ema50 < ema200:
            return {
                "regime": "DOWNTREND",
                "score": 0.40
            }

        # Sideways / Range
        return {
            "regime": "RANGE",
            "score": 0.60
        }
