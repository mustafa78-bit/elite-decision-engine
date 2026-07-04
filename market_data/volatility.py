class VolatilityEngine:

    def score(self, indicators):

        atr = indicators["atr"]
        ema20 = indicators["ema20"]

        volatility = atr / ema20

        if volatility < 0.003:
            score = 1.0

        elif volatility < 0.006:
            score = 0.8

        elif volatility < 0.010:
            score = 0.6

        elif volatility < 0.020:
            score = 0.4

        else:
            score = 0.2

        return {
            "volatility": round(volatility, 5),
            "score": score,
        }
