class TPSLEngine:

    def calculate(self, entry, atr, side):

        # ATR yoksa varsayılan değer
        if atr <= 0:
            atr = entry * 0.01

        if side.upper() == "LONG":

            stop = entry - (atr * 1.5)

            tp1 = entry + (atr * 2.0)

            tp2 = entry + (atr * 4.0)

        else:

            stop = entry + (atr * 1.5)

            tp1 = entry - (atr * 2.0)

            tp2 = entry - (atr * 4.0)

        risk = abs(entry - stop)
        reward = abs(tp1 - entry)

        rr = reward / risk if risk > 0 else 0

        return {
            "entry": round(entry, 4),
            "stop": round(stop, 4),
            "tp1": round(tp1, 4),
            "tp2": round(tp2, 4),
            "rr": round(rr, 2),
        }
