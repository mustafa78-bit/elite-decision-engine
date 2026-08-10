"""Tests for BinanceProvider."""

import time
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
import requests

from market.provider.binance import BinanceProvider


class TestBinanceProvider:

    def setup_method(self):
        self.mock_fallback = MagicMock()
        self.provider = BinanceProvider(
            fallback_provider=self.mock_fallback,
        )
        self.provider._session = MagicMock()

    @patch("time.sleep")
    def test_get_ohlcv_success(self, mock_sleep):
        now_ms = int(time.time() * 1000)
        mock_response = MagicMock()
        mock_response.json.return_value = [
            [now_ms, "100.0", "102.0", "99.0", "101.0", "1000.0", now_ms + 59999, "101000.0", 300, "500.0", "50500.0", "0"]
        ]
        self.provider._session.get.return_value = mock_response

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)

        assert not df.empty
        assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
        assert df["timestamp"].iloc[0] == now_ms
        assert df["open"].iloc[0] == 100.0
        assert df["high"].iloc[0] == 102.0
        assert df["low"].iloc[0] == 99.0
        assert df["close"].iloc[0] == 101.0
        assert df["volume"].iloc[0] == 1000.0

        self.provider._session.get.assert_called_once_with(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": "BTCUSDT", "interval": "1h", "limit": 100},
            timeout=20
        )

    @patch("time.sleep")
    def test_get_ohlcv_stale_data(self, mock_sleep):
        # 3 hours ago in milliseconds
        stale_ms = int((time.time() - 10800) * 1000)
        mock_response = MagicMock()
        mock_response.json.return_value = [
            [stale_ms, "100.0", "102.0", "99.0", "101.0", "1000.0", stale_ms + 59999, "101000.0", 300, "500.0", "50500.0", "0"]
        ]
        self.provider._session.get.return_value = mock_response

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)
        assert df.empty

    @patch("time.sleep")
    def test_get_ohlcv_retries_and_succeeds(self, mock_sleep):
        now_ms = int(time.time() * 1000)
        mock_response = MagicMock()
        mock_response.json.return_value = [
            [now_ms, "100.0", "102.0", "99.0", "101.0", "1000.0", now_ms + 59999, "101000.0", 300, "500.0", "50500.0", "0"]
        ]
        # Raise Timeout once, then succeed
        self.provider._session.get.side_effect = [
            requests.Timeout("Timeout error"),
            mock_response
        ]

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)
        assert not df.empty
        assert self.provider._session.get.call_count == 2
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    def test_get_ohlcv_retries_exhausted(self, mock_sleep):
        self.provider._session.get.side_effect = requests.Timeout("Timeout error")

        with pytest.raises(requests.Timeout):
            self.provider.get_ohlcv("BTCUSDT", "1h", 100)

        assert self.provider._session.get.call_count == 3
        assert mock_sleep.call_count == 2

    def test_get_ticker_empty(self):
        with patch.object(self.provider, "get_ohlcv", return_value=pd.DataFrame()):
            result = self.provider.get_ticker("BTCUSDT")
            assert result["price"] == 0.0

    def test_get_ticker_success(self):
        now_ms = int(time.time() * 1000)
        df = pd.DataFrame({
            "timestamp": [now_ms],
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [1000.0],
        })
        with patch.object(self.provider, "get_ohlcv", return_value=df):
            result = self.provider.get_ticker("BTCUSDT")
            assert result["symbol"] == "BTCUSDT"
            assert result["price"] == 101.0
            assert result["open"] == 100.0
            assert result["high"] == 102.0
            assert result["low"] == 99.0
            assert result["volume"] == 1000.0

    def test_delegated_methods(self):
        self.mock_fallback.get_funding.return_value = {"rate": 0.01}
        assert self.provider.get_funding("BTCUSDT") == {"rate": 0.01}
        self.mock_fallback.get_funding.assert_called_once_with("BTCUSDT")

        self.mock_fallback.get_open_interest.return_value = {"open_interest": 10000}
        assert self.provider.get_open_interest("BTCUSDT") == {"open_interest": 10000}
        self.mock_fallback.get_open_interest.assert_called_once_with("BTCUSDT")

        self.mock_fallback.get_orderbook.return_value = {"bids": []}
        assert self.provider.get_orderbook("BTCUSDT", depth=5) == {"bids": []}
        self.mock_fallback.get_orderbook.assert_called_once_with("BTCUSDT", depth=5)

        self.mock_fallback.get_trades.return_value = [{"id": 1}]
        assert self.provider.get_trades("BTCUSDT", limit=50) == [{"id": 1}]
        self.mock_fallback.get_trades.assert_called_once_with("BTCUSDT", limit=50)
