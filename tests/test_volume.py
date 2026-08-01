from market_data.collector import HyperliquidCollector
from market_data.volume import VolumeEngine

collector = HyperliquidCollector()
volume = VolumeEngine()

df = collector.get_ohlcv("BTC", "1h")

print(volume.score(df))
