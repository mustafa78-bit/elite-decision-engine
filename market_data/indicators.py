import pandas_ta as ta


class IndicatorEngine:

    def calculate(self, df):

        df = df.copy()

        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)

        df.ta.rsi(length=14, append=True)

        df.ta.atr(length=14, append=True)

        latest = df.iloc[-1]

        return {
            "ema20": float(latest["EMA_20"]),
            "ema50": float(latest["EMA_50"]),
            "ema200": float(latest["EMA_200"]),
            "rsi": float(latest["RSI_14"]),
            "atr": float(latest["ATRr_14"]),
        }
