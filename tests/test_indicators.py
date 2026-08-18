import pandas as pd

from market_data.indicators import IndicatorEngine


class TestIndicatorEngineCalculate:
    def test_calculate_returns_expected_keys(self):
        df = pd.DataFrame({
            "timestamp": range(300),
            "open": [100.0 + i * 0.1 for i in range(300)],
            "high": [101.0 + i * 0.1 for i in range(300)],
            "low": [99.0 + i * 0.1 for i in range(300)],
            "close": [100.5 + i * 0.1 for i in range(300)],
            "volume": [10.0 for _ in range(300)],
        })
        values = IndicatorEngine().calculate(df)
        assert set(values.keys()) == {"ema20", "ema50", "ema200", "rsi", "atr"}
        assert all(isinstance(v, float) for v in values.values())

    def test_calculate_returns_neutral_values_for_empty_df(self):
        # Regression: an empty df (e.g. a provider deeming its latest candle
        # too stale and returning nothing) previously crashed here -- pandas_ta's
        # df.ta.ema() calls df.columns.str.match() internally, which raises
        # on an empty DataFrame's default integer-typed column index.
        values = IndicatorEngine().calculate(pd.DataFrame())
        assert values == {"ema20": 0.0, "ema50": 0.0, "ema200": 0.0, "rsi": 50.0, "atr": 0.0}

    def test_calculate_returns_neutral_values_for_none(self):
        values = IndicatorEngine().calculate(None)
        assert values == {"ema20": 0.0, "ema50": 0.0, "ema200": 0.0, "rsi": 50.0, "atr": 0.0}
