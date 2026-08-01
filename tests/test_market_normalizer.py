"""Tests for market data normalizer."""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from exchange.models import Candle
from market_data.normalizer.normalizer import (
    deduplicate_candles,
    merge_candles,
    normalize_candle_from_df,
    normalize_ticker,
)
from market_data.normalizer.symbols import (
    from_exchange_symbol,
    standard_symbol,
    to_exchange_symbol,
)


class TestSymbolNormalizer:
    def test_to_exchange_hyperliquid(self):
        assert to_exchange_symbol("BTC", "hyperliquid") == "BTC"

    def test_to_exchange_binance(self):
        assert to_exchange_symbol("BTC", "binance") == "BTCUSDT"

    def test_from_exchange_hyperliquid(self):
        assert from_exchange_symbol("BTC", "hyperliquid") == "BTC"

    def test_from_exchange_binance(self):
        assert from_exchange_symbol("BTCUSDT", "binance") == "BTC"

    def test_standard_suffix_removal(self):
        assert standard_symbol("BTCUSDT") == "BTC"
        assert standard_symbol("ETHUSD") == "ETH"
        assert standard_symbol("SOLUSDC") == "SOL"

    def test_standard_no_suffix(self):
        assert standard_symbol("BTC") == "BTC"


class TestNormalizer:
    def test_normalize_candle_from_df(self):
        df = pd.DataFrame({
            "timestamp": [1700000000000],
            "open": [50000.0],
            "high": [51000.0],
            "low": [49000.0],
            "close": [50500.0],
            "volume": [1000.0],
        })
        candles = normalize_candle_from_df(df, "BTC", "1h")
        assert len(candles) == 1
        assert candles[0].symbol == "BTC"
        assert candles[0].open == Decimal("50000")
        assert candles[0].close == Decimal("50500")

    def test_normalize_ticker(self):
        ticker = normalize_ticker(symbol="BTC", last=50000.0, volume_24h=10000.0, change_24h=2.5)
        assert ticker.symbol == "BTC"
        assert ticker.last == Decimal("50000")
        assert ticker.change_24h == Decimal("2.5")

    def test_merge_candles(self):
        c1 = Candle(symbol="BTC", timeframe="1h", open=Decimal("100"), high=Decimal("110"), low=Decimal("90"), close=Decimal("105"), volume=Decimal("1000"), timestamp=datetime(2024, 1, 1, 1, 0))
        c2 = Candle(symbol="BTC", timeframe="1h", open=Decimal("105"), high=Decimal("115"), low=Decimal("95"), close=Decimal("110"), volume=Decimal("1500"), timestamp=datetime(2024, 1, 1, 2, 0))
        merged = merge_candles([[c2], [c1]])
        assert len(merged) == 2
        assert merged[0].timestamp.hour == 1
        assert merged[1].timestamp.hour == 2

    def test_deduplicate_candles(self):
        ts = datetime(2024, 1, 1, 1, 0)
        c1 = Candle(symbol="BTC", timeframe="1h", open=Decimal("100"), high=Decimal("110"), low=Decimal("90"), close=Decimal("105"), volume=Decimal("1000"), timestamp=ts)
        c2 = Candle(symbol="BTC", timeframe="1h", open=Decimal("100"), high=Decimal("110"), low=Decimal("90"), close=Decimal("105"), volume=Decimal("1000"), timestamp=ts)
        deduped = deduplicate_candles([c1, c2])
        assert len(deduped) == 1
