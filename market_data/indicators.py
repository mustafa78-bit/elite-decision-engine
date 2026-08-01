import pandas_ta as ta


class IndicatorEngine:

    def _find_atr_col(self, df):
        for col in df.columns:
            upper = col.upper()
            if upper.startswith("ATR"):
                return col
        return None

    def calculate(self, df):

        df = df.copy()

        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)

        df.ta.rsi(length=14, append=True)

        df.ta.atr(length=14, append=True)

        latest = df.iloc[-1]

        atr_col = self._find_atr_col(df)
        if atr_col is None:
            raise KeyError("No ATR column found in DataFrame after pandas_ta computation")

        return {
            "ema20": float(latest["EMA_20"]),
            "ema50": float(latest["EMA_50"]),
            "ema200": float(latest["EMA_200"]),
            "rsi": float(latest["RSI_14"]),
            "atr": float(latest[atr_col]),
        }
