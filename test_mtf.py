from market_data.mtf import MTFEngine

mtf = MTFEngine()

print("BTC LONG :", mtf.score("BTCUSDT", "LONG"))
print("BTC SHORT:", mtf.score("BTCUSDT", "SHORT"))
print("ETH LONG :", mtf.score("ETHUSDT", "LONG"))
