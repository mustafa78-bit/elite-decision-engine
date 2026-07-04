from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine

collector = HyperliquidCollector()
indicator = IndicatorEngine()
vol = VolatilityEngine()

df = collector.get_ohlcv("BTC", "1h")

values = indicator.calculate(df)

print(vol.score(values))
