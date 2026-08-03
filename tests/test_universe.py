"""Tests for the dynamic coin universe provider."""

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from config import COIN_UNIVERSE_SIZE
from market_data.universe import BinanceUniverseProvider, get_top_volume_symbols
from scanner.core import OpportunityScanner


@pytest.fixture
def mock_binance_data():
    return [
        {"symbol": "BTCUSDT", "quoteVolume": "100000000.0"},
        {"symbol": "ETHUSDT", "quoteVolume": "50000000.0"},
        {"symbol": "SOLUSDT", "quoteVolume": "25000000.0"},
        {"symbol": "DOGEUSDT", "quoteVolume": "10000000.0"},
        {"symbol": "ADAUSDT", "quoteVolume": "invalid_float"},
        {"symbol": "NOTUSDT", "quoteVolume": None},
        {"symbol": "BTCDUSD", "quoteVolume": "99999999.0"},  # Non-USDT pair
        {"symbol": "LINKUSDT", "quoteVolume": "15000000.0"},
    ]


def test_provider_default_fallback_on_immediate_failure():
    """Ensure that if the first fetch fails, we get default symbols."""
    provider = BinanceUniverseProvider(cache_interval=60, url="http://fake-url")
    with patch("requests.get", side_effect=requests.RequestException("Network down")):
        symbols = provider.get_top_volume_symbols()
        assert symbols == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def test_provider_success_filtering_sorting_limiting(mock_binance_data):
    """Ensure ticker data is filtered to USDT pairs, sorted by quoteVolume desc, and limited."""
    provider = BinanceUniverseProvider(cache_interval=60)
    mock_response = MagicMock()
    mock_response.json.return_value = mock_binance_data
    mock_response.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_response) as mock_get:
        # Ask for top 3 USDT pairs
        symbols = provider.get_top_volume_symbols(n=3)
        mock_get.assert_called_once()
        # Sorted USDT pairs by volume should be: BTCUSDT (100M), ETHUSDT (50M), SOLUSDT (25M), LINKUSDT (15M), DOGEUSDT (10M)
        # ADAUSDT and NOTUSDT are invalid, BTCDUSD is non-USDT.
        # Top 3: ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        assert symbols == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def test_provider_custom_n_limit(mock_binance_data):
    """Ensure custom limits are respected and we can request more/fewer symbols."""
    provider = BinanceUniverseProvider(cache_interval=60)
    mock_response = MagicMock()
    mock_response.json.return_value = mock_binance_data
    mock_response.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_response):
        symbols_all = provider.get_top_volume_symbols(n=10)
        # Max valid filtered USDT is: BTCUSDT, ETHUSDT, SOLUSDT, LINKUSDT, DOGEUSDT (5 symbols)
        assert len(symbols_all) == 5
        assert symbols_all == ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "DOGEUSDT"]

        # Request just top 2
        symbols_two = provider.get_top_volume_symbols(n=2)
        assert symbols_two == ["BTCUSDT", "ETHUSDT"]


def test_provider_caching_behavior(mock_binance_data):
    """Ensure symbols are cached and not re-fetched within the interval."""
    provider = BinanceUniverseProvider(cache_interval=3600)  # 1 hour
    mock_response = MagicMock()
    mock_response.json.return_value = mock_binance_data
    mock_response.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_response) as mock_get:
        # First call updates cache
        first_symbols = provider.get_top_volume_symbols(n=3)
        assert first_symbols == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        assert mock_get.call_count == 1

        # Second call should use cache (no HTTP call)
        second_symbols = provider.get_top_volume_symbols(n=3)
        assert second_symbols == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        assert mock_get.call_count == 1  # Still 1


def test_provider_cache_expiry(mock_binance_data):
    """Ensure cache expires and triggers a re-fetch when interval has elapsed."""
    provider = BinanceUniverseProvider(cache_interval=10)  # 10s
    mock_response = MagicMock()
    mock_response.json.return_value = mock_binance_data
    mock_response.raise_for_status = MagicMock()

    start_time = time.time()

    with patch("requests.get", return_value=mock_response) as mock_get:
        # First call (at t+0): fetches
        with patch("time.time", return_value=start_time):
            provider.get_top_volume_symbols(n=3)
        assert mock_get.call_count == 1

        # Second call (at t+5, < cache_interval): cached
        with patch("time.time", return_value=start_time + 5):
            provider.get_top_volume_symbols(n=3)
        assert mock_get.call_count == 1

        # Third call (at t+15, > cache_interval): re-fetches
        with patch("time.time", return_value=start_time + 15):
            provider.get_top_volume_symbols(n=3)
        assert mock_get.call_count == 2


def test_provider_fallback_to_stale_cache_on_failure(mock_binance_data):
    """Verify that if cache is stale but API call fails, we return the stale cache instead of hardcoded defaults."""
    provider = BinanceUniverseProvider(cache_interval=10)
    mock_response = MagicMock()
    mock_response.json.return_value = mock_binance_data
    mock_response.raise_for_status = MagicMock()

    start_time = time.time()
    # First, populate cache successfully
    with patch("requests.get", return_value=mock_response):
        res1 = provider.get_top_volume_symbols(n=4)
        assert res1 == ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT"]

    # Now, time moves forward past cache interval, and next API call fails.
    # It should fallback to the cached list we just fetched!
    with patch("requests.get", side_effect=requests.RequestException("Timeout")), \
         patch("time.time", return_value=start_time + 20):
        res2 = provider.get_top_volume_symbols(n=4)
        assert res2 == ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT"]


def test_global_get_top_volume_symbols_and_scanner_integration(mock_binance_data, monkeypatch):
    """Test global helper get_top_volume_symbols and OpportunityScanner default initialization.

    Uses a fresh BinanceUniverseProvider swapped into the module-level singleton for
    the duration of this test, then restores the original. Without this, this test
    (uniquely among this file's tests) mutates the shared process-wide singleton's
    cache, leaking mocked state into any other test in the suite that constructs an
    OpportunityScanner() without explicit symbols - or, worse, causing an unrelated
    test to be the first to touch the real (unmocked) singleton and make a live
    network call to Binance.
    """
    import market_data.universe as universe_module

    fresh_provider = BinanceUniverseProvider(cache_interval=universe_module.CACHE_INTERVAL_SECONDS)
    monkeypatch.setattr(universe_module, "_provider", fresh_provider)

    mock_response = MagicMock()
    mock_response.json.return_value = mock_binance_data
    mock_response.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_response):
        # Test helper function
        symbols = get_top_volume_symbols(n=2)
        assert symbols == ["BTCUSDT", "ETHUSDT"]

        # Test OpportunityScanner without passing symbols gets dynamic universe
        # Let's mock get_top_volume_symbols to make sure scanner uses it
        with patch("scanner.core.get_top_volume_symbols", return_value=["BTCUSDT", "ETHUSDT"]) as mock_dyn:
            scanner = OpportunityScanner()
            assert scanner.symbols == ["BTCUSDT", "ETHUSDT"]
            mock_dyn.assert_called_once()

            # If explicit symbols are passed, keep them
            scanner_override = OpportunityScanner(symbols=["SOLUSDT"])
            assert scanner_override.symbols == ["SOLUSDT"]
