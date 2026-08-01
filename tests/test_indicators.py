from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine

collector = HyperliquidCollector()
engine = IndicatorEngine()

df = collector.get_ohlcv("BTC", "1h")

values = engine.calculate(df)

print(values)
