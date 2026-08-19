"""Tests for BybitProvider."""

import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from market.provider.bybit import BybitProvider


def _kline_row(ts_ms: int, close: str = "101.0") -> list:
    """One Bybit V5 kline row: [startTime, open, high, low, close, volume, turnover]."""
    return [str(ts_ms), "100.0", "102.0", "99.0", close, "1000.0", "101000.0"]


def _bybit_response(rows: list, ret_code: int = 0, ret_msg: str = "OK") -> dict:
    return {"retCode": ret_code, "retMsg": ret_msg, "result": {"list": rows}}


class TestBybitProvider:

    def setup_method(self):
        self.mock_fallback = MagicMock()
        self.provider = BybitProvider(fallback_provider=self.mock_fallback)
        self.provider._session = MagicMock()

    # -- interval mapping -------------------------------------------------

    @patch("time.sleep")
    def test_get_ohlcv_success_uses_mapped_interval(self, mock_sleep):
        now_ms = int(time.time() * 1000)
        mock_response = MagicMock()
        mock_response.json.return_value = _bybit_response([_kline_row(now_ms)])
        self.provider._session.get.return_value = mock_response

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)

        assert not df.empty
        self.provider._session.get.assert_called_once_with(
            "https://api.bybit.com/v5/market/kline",
            params={"category": "linear", "symbol": "BTCUSDT", "interval": "60", "limit": 100},
            timeout=20,
        )

    @pytest.mark.parametrize("timeframe,expected", [
        ("1m", "1"), ("5m", "5"), ("15m", "15"), ("30m", "30"),
        ("1h", "60"), ("4h", "240"), ("1d", "D"), ("1w", "W"),
    ])
    @patch("time.sleep")
    def test_all_supported_timeframes_map_correctly(self, mock_sleep, timeframe, expected):
        now_ms = int(time.time() * 1000)
        mock_response = MagicMock()
        mock_response.json.return_value = _bybit_response([_kline_row(now_ms)])
        self.provider._session.get.return_value = mock_response

        self.provider.get_ohlcv("BTCUSDT", timeframe, 100)

        _, kwargs = self.provider._session.get.call_args
        assert kwargs["params"]["interval"] == expected

    def test_unsupported_timeframe_raises(self):
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            self.provider.get_ohlcv("BTCUSDT", "2h", 100)

    # -- ordering / shape ---------------------------------------------------

    @patch("time.sleep")
    def test_newest_first_response_is_reversed_to_ascending(self, mock_sleep):
        now_ms = int(time.time() * 1000)
        older_ms = now_ms - 60_000
        # Bybit returns newest-first.
        rows = [_kline_row(now_ms, close="103.0"), _kline_row(older_ms, close="101.0")]
        mock_response = MagicMock()
        mock_response.json.return_value = _bybit_response(rows)
        self.provider._session.get.return_value = mock_response

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)

        assert list(df["timestamp"]) == [older_ms, now_ms]
        assert df["close"].iloc[-1] == 103.0

    @patch("time.sleep")
    def test_get_ohlcv_column_shape_and_dtypes(self, mock_sleep):
        now_ms = int(time.time() * 1000)
        mock_response = MagicMock()
        mock_response.json.return_value = _bybit_response([_kline_row(now_ms)])
        self.provider._session.get.return_value = mock_response

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)

        assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
        assert df["timestamp"].dtype == "int64"
        for col in ["open", "high", "low", "close", "volume"]:
            assert df[col].dtype == "float64"
        assert df["open"].iloc[0] == 100.0
        assert df["high"].iloc[0] == 102.0
        assert df["low"].iloc[0] == 99.0
        assert df["close"].iloc[0] == 101.0
        assert df["volume"].iloc[0] == 1000.0

    # -- error handling -------------------------------------------------

    @patch("time.sleep")
    def test_ret_code_nonzero_treated_as_error_and_retried(self, mock_sleep):
        now_ms = int(time.time() * 1000)
        error_response = MagicMock()
        error_response.json.return_value = _bybit_response([], ret_code=10001, ret_msg="params error")
        ok_response = MagicMock()
        ok_response.json.return_value = _bybit_response([_kline_row(now_ms)])
        self.provider._session.get.side_effect = [error_response, ok_response]

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)

        assert not df.empty
        assert self.provider._session.get.call_count == 2

    @patch("time.sleep")
    def test_empty_klines_returns_empty_dataframe(self, mock_sleep):
        mock_response = MagicMock()
        mock_response.json.return_value = _bybit_response([])
        self.provider._session.get.return_value = mock_response

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)
        assert df.empty

    @patch("time.sleep")
    def test_get_ohlcv_stale_data(self, mock_sleep):
        stale_ms = int((time.time() - 10800) * 1000)  # 3 hours ago
        mock_response = MagicMock()
        mock_response.json.return_value = _bybit_response([_kline_row(stale_ms)])
        self.provider._session.get.return_value = mock_response

        df = self.provider.get_ohlcv("BTCUSDT", "1h", 100)
        assert df.empty

    @patch("time.sleep")
    def test_get_ohlcv_retries_and_succeeds(self, mock_sleep):
        now_ms = int(time.time() * 1000)
        mock_response = MagicMock()
        mock_response.json.return_value = _bybit_response([_kline_row(now_ms)])
        self.provider._session.get.side_effect = [
            requests.Timeout("Timeout error"),
            mock_response,
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

    # -- get_ticker -------------------------------------------------

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

    # -- fallback delegation -------------------------------------------------

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
