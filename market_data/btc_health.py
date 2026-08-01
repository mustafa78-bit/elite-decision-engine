from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine


class BTCHealth:

    def __init__(self, collector=None):
        self.collector = collector or HyperliquidCollector()
        self.indicators = IndicatorEngine()

    def score(self):

        df = self.collector.get_ohlcv(
            symbol="BTC",
            timeframe="1h",
        )

        values = self.indicators.calculate(df)

        score = 0.0

        if values["ema20"] > values["ema50"]:
            score += 0.30

        if values["ema50"] > values["ema200"]:
            score += 0.40

        if values["rsi"] > 50:
            score += 0.30

        return round(score, 2)
