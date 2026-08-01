"""Tests for HyperliquidProvider."""

from unittest.mock import MagicMock
import pandas as pd

from market.provider import HyperliquidProvider


class TestHyperliquidProvider:

    def setup_method(self):
        self.mock_collector = MagicMock()
        self.mock_funding = MagicMock()
        self.mock_oi = MagicMock()
        self.provider = HyperliquidProvider(
            collector=self.mock_collector,
            funding_collector=self.mock_funding,
            oi_collector=self.mock_oi,
        )

    def test_get_ohlcv_delegates(self):
        df = pd.DataFrame({"close": [100.0, 101.0]})
        self.mock_collector.get_ohlcv.return_value = df
        result = self.provider.get_ohlcv("BTC", "1h", 100)
        assert result is df
        self.mock_collector.get_ohlcv.assert_called_with(symbol="BTC", timeframe="1h", limit=100)

    def test_get_ticker_empty(self):
        self.mock_collector.get_ohlcv.return_value = pd.DataFrame()
        result = self.provider.get_ticker("BTC")
        assert result["price"] == 0.0

    def test_get_ticker_with_data(self):
        df = pd.DataFrame({
            "close": [101.0], "open": [100.0],
            "high": [102.0], "low": [99.0], "volume": [1000.0],
        })
        self.mock_collector.get_ohlcv.return_value = df
        result = self.provider.get_ticker("BTC")
        assert result["symbol"] == "BTC"
        assert result["price"] == 101.0

    def test_get_funding_handles_error(self):
        self.mock_funding.fetch_for_symbol.side_effect = Exception("API error")
        result = self.provider.get_funding("BTC")
        assert "error" in result
        assert result["rate"] == 0.0

    def test_get_open_interest_handles_error(self):
        self.mock_oi.fetch_with_trend.side_effect = Exception("API error")
        result = self.provider.get_open_interest("ETH")
        assert "error" in result
