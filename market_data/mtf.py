from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine


class MTFEngine:

    def __init__(self):
        self.collector = HyperliquidCollector()
        self.indicators = IndicatorEngine()

    def score(self, symbol, side):

        coin = symbol.replace("USDT", "")

        timeframes = ["15m", "1h", "4h"]

        score = 0

        for tf in timeframes:

            df = self.collector.get_ohlcv(
                symbol=coin,
                timeframe=tf,
            )

            ind = self.indicators.calculate(df)

            if side == "LONG":
                if ind["ema20"] > ind["ema50"] > ind["ema200"]:
                    score += 1
            else:
                if ind["ema20"] < ind["ema50"] < ind["ema200"]:
                    score += 1

        return round(score / len(timeframes), 2)
