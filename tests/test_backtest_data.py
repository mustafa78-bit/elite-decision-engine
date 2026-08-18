"""Tests for backtest/data.py -- real historical OHLCV fetch + local
persistence (data/historical/*.csv, gitignored, never sent externally).
See its module docstring for why: council/fundamental_gate.py's parameter
search needs real historical price data to backtest against."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import backtest.data as backtest_data
from backtest.data import fetch_all_historical, fetch_symbol_history


def _fake_ohlcv(n: int = 5) -> pd.DataFrame:
    return pd.DataFrame({
        "timestamp": list(range(n)),
        "open": [100.0] * n,
        "high": [101.0] * n,
        "low": [99.0] * n,
        "close": [100.5] * n,
        "volume": [10.0] * n,
    })


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    """Never touch the real data/historical/ directory from tests."""
    monkeypatch.setattr(backtest_data, "DATA_DIR", tmp_path)
    yield


class TestFetchSymbolHistory:

    def test_fetches_and_saves_when_no_cache(self):
        mock_provider = MagicMock()
        mock_provider.get_ohlcv.return_value = _fake_ohlcv()

        df = fetch_symbol_history("BTCUSDT", provider=mock_provider)

        assert len(df) == 5
        mock_provider.get_ohlcv.assert_called_once()
        saved = backtest_data._file_path("BTCUSDT", "1h")
        assert saved.exists()

    def test_reuses_fresh_cache_without_refetching(self):
        mock_provider = MagicMock()
        mock_provider.get_ohlcv.return_value = _fake_ohlcv()

        fetch_symbol_history("BTCUSDT", provider=mock_provider)
        fetch_symbol_history("BTCUSDT", provider=mock_provider)

        # Second call should hit the local cache, not the provider again.
        mock_provider.get_ohlcv.assert_called_once()

    def test_force_refetches_even_when_cache_is_fresh(self):
        mock_provider = MagicMock()
        mock_provider.get_ohlcv.return_value = _fake_ohlcv()

        fetch_symbol_history("BTCUSDT", provider=mock_provider)
        fetch_symbol_history("BTCUSDT", provider=mock_provider, force=True)

        assert mock_provider.get_ohlcv.call_count == 2

    def test_empty_provider_response_returns_empty_df_without_saving(self):
        mock_provider = MagicMock()
        mock_provider.get_ohlcv.return_value = pd.DataFrame()

        df = fetch_symbol_history("MKRUSDT", provider=mock_provider)

        assert df.empty
        assert not backtest_data._file_path("MKRUSDT", "1h").exists()

    def test_provider_exception_returns_empty_df_not_raise(self):
        mock_provider = MagicMock()
        mock_provider.get_ohlcv.side_effect = Exception("network boom")

        df = fetch_symbol_history("BTCUSDT", provider=mock_provider)

        assert df.empty


class TestFetchAllHistorical:

    def test_fetches_full_universe_plus_btc(self):
        mock_provider = MagicMock()
        mock_provider.get_ohlcv.return_value = _fake_ohlcv()

        with patch("backtest.data.MultiProvider", return_value=mock_provider):
            results = fetch_all_historical(symbols=["ETHUSDT"])

        # BTC gets appended even when not explicitly requested (needed for
        # BTCHealth reconstruction -- see fetch_all_historical()'s docstring).
        assert "ETHUSDT" in results
        assert "BTCUSDT" in results
        assert all(not df.empty for df in results.values())

    def test_one_bad_symbol_does_not_break_the_batch(self):
        mock_provider = MagicMock()

        def side_effect(symbol, **kwargs):
            if symbol == "MKRUSDT":
                raise Exception("dead pair")
            return _fake_ohlcv()

        mock_provider.get_ohlcv.side_effect = side_effect

        with patch("backtest.data.MultiProvider", return_value=mock_provider):
            results = fetch_all_historical(symbols=["MKRUSDT", "ETHUSDT"])

        assert results["MKRUSDT"].empty
        assert not results["ETHUSDT"].empty
