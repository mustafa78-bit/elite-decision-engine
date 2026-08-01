from market_data.collector import HyperliquidCollector

collector = HyperliquidCollector()

df = collector.get_ohlcv(
    symbol="BTC",
    timeframe="1h",
)

print(df.head())
print()
print(df.tail())
print()
print("Rows:", len(df))
print("Columns:", list(df.columns))
