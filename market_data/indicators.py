import pandas_ta as ta


class IndicatorEngine:

    def _find_atr_col(self, df):
        for col in df.columns:
            upper = col.upper()
            if upper.startswith("ATR"):
                return col
        return None

    def calculate(self, df):
        # An empty df (e.g. a provider deeming its latest candle too stale
        # and returning nothing, or a genuine fetch failure) previously
        # crashed here: pandas_ta's df.ta.ema() calls df.columns.str.match()
        # internally, which raises on an empty DataFrame's default
        # integer-typed column index rather than a string one. Return
        # neutral values instead of propagating -- callers already treat a
        # flat ema20==ema50==ema200 as "no trend confirmation", which is the
        # honest answer when there's no real data to compute one from.
        if df is None or df.empty:
            return {"ema20": 0.0, "ema50": 0.0, "ema200": 0.0, "rsi": 50.0, "atr": 0.0}

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
