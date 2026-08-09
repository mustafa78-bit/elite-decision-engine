"""Tests for HyperliquidProvider -- the single entry point market/services/
market_data.py uses for all market data, wrapping the lower-level collectors.
"""

from unittest.mock import MagicMock

import pandas as pd

from market.provider.hyperliquid import HyperliquidProvider


class TestHyperliquidProviderGetOhlcv:

    def test_strips_usdt_suffix_before_calling_collector(self):
        # Regression: get_ohlcv() used to pass ticker-style symbols
        # ("ETHUSDT", as scanner/core.py's universe provides) straight
        # through to the collector, which expects Hyperliquid's bare coin
        # id ("ETH") -- every non-bare symbol 500'd against the real API.
        # get_funding()/get_open_interest() already stripped "USDT"; this
        # brings get_ohlcv() in line with them.
        mock_collector = MagicMock()
        mock_collector.get_ohlcv.return_value = pd.DataFrame({"close": [1.0]})
        provider = HyperliquidProvider(collector=mock_collector)

        provider.get_ohlcv(symbol="ETHUSDT", timeframe="1h", limit=5)

        mock_collector.get_ohlcv.assert_called_once_with(symbol="ETH", timeframe="1h", limit=5)

    def test_bare_symbol_passes_through_unchanged(self):
        mock_collector = MagicMock()
        mock_collector.get_ohlcv.return_value = pd.DataFrame({"close": [1.0]})
        provider = HyperliquidProvider(collector=mock_collector)

        provider.get_ohlcv(symbol="BTC", timeframe="1h", limit=5)

        mock_collector.get_ohlcv.assert_called_once_with(symbol="BTC", timeframe="1h", limit=5)


class TestHyperliquidProviderGetTicker:

    def test_get_ticker_strips_usdt_via_get_ohlcv(self):
        mock_collector = MagicMock()
        mock_collector.get_ohlcv.return_value = pd.DataFrame({
            "open": [100.0], "high": [110.0], "low": [90.0], "close": [105.0], "volume": [10.0],
        })
        provider = HyperliquidProvider(collector=mock_collector)

        ticker = provider.get_ticker("SOLUSDT")

        mock_collector.get_ohlcv.assert_called_once_with(symbol="SOL", timeframe="1h", limit=2)
        assert ticker["price"] == 105.0
