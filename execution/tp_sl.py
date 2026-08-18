from typing import Optional

from config import ATR_MULTIPLIER, TP1_ATR_MULTIPLIER


class TPSLEngine:

    def __init__(self, atr_multiplier: float | None = None, tp1_atr_multiplier: float | None = None) -> None:
        self.atr_multiplier = atr_multiplier if atr_multiplier is not None else ATR_MULTIPLIER
        self.tp1_atr_multiplier = tp1_atr_multiplier if tp1_atr_multiplier is not None else TP1_ATR_MULTIPLIER

    def calculate(self, entry, atr, side):
        if entry is None or entry == 0:
            raise ValueError(f"Cannot calculate TP/SL with entry={entry}")

        # Fallback to 1% of entry when ATR is zero or negative
        if atr <= 0:
            atr = entry * 0.01

        if side.upper() == "LONG":

            stop = entry - (atr * self.atr_multiplier)

            tp1 = entry + (atr * self.tp1_atr_multiplier)

            tp2 = entry + (atr * 4.0)

        else:

            stop = entry + (atr * self.atr_multiplier)

            tp1 = entry - (atr * self.tp1_atr_multiplier)

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
