"""Tests for MultiProvider's routing + rate-limiting."""

from unittest.mock import MagicMock

import pandas as pd

from config import FIXED_COIN_UNIVERSE, SYMBOL_PROVIDER_ASSIGNMENT
from market.provider.multi import MultiProvider


class TestSymbolProviderAssignment:

    def test_every_fixed_universe_symbol_has_an_assignment(self):
        for symbol in FIXED_COIN_UNIVERSE:
            assert symbol in SYMBOL_PROVIDER_ASSIGNMENT
            assert SYMBOL_PROVIDER_ASSIGNMENT[symbol] in ("hyperliquid", "binance", "bybit")

    def test_hyperliquid_carries_the_smallest_share(self):
        # Rebalanced 2026-08-19 (Bybit added as a 3rd provider) specifically
        # because Hyperliquid kept showing real, recurring 429s even at a
        # roughly-even 2-way split -- it must now carry the smallest share
        # of the three, not the largest or an equal share.
        counts = {"hyperliquid": 0, "binance": 0, "bybit": 0}
        for v in SYMBOL_PROVIDER_ASSIGNMENT.values():
            counts[v] += 1
        assert counts["hyperliquid"] < counts["binance"]
        assert counts["hyperliquid"] < counts["bybit"]

    def test_binance_and_bybit_share_is_roughly_even(self):
        counts = {"hyperliquid": 0, "binance": 0, "bybit": 0}
        for v in SYMBOL_PROVIDER_ASSIGNMENT.values():
            counts[v] += 1
        assert abs(counts["binance"] - counts["bybit"]) <= 1

    def test_btc_stays_on_hyperliquid(self):
        # BTC is the most-tested path -- deliberately kept on Hyperliquid
        # through the rebalance rather than moved to the new provider.
        assert SYMBOL_PROVIDER_ASSIGNMENT["BTCUSDT"] == "hyperliquid"


class TestMultiProviderRouting:

    def setup_method(self):
        self.mock_hl = MagicMock()
        self.mock_binance = MagicMock()
        self.mock_bybit = MagicMock()
        self.provider = MultiProvider(
            hyperliquid_provider=self.mock_hl,
            binance_provider=self.mock_binance,
            bybit_provider=self.mock_bybit,
            requests_per_second=1000.0,  # effectively unthrottled for routing tests
        )
        self._mocks = {
            "hyperliquid": self.mock_hl,
            "binance": self.mock_binance,
            "bybit": self.mock_bybit,
        }

    def test_each_fixed_symbol_resolves_to_its_assigned_provider(self):
        for mock in self._mocks.values():
            mock.get_ticker.return_value = {"symbol": "x", "price": 1.0}

        for symbol, assignment in SYMBOL_PROVIDER_ASSIGNMENT.items():
            for mock in self._mocks.values():
                mock.reset_mock()

            self.provider.get_ticker(symbol)

            for name, mock in self._mocks.items():
                if name == assignment:
                    mock.get_ticker.assert_called_once_with(symbol)
                else:
                    mock.get_ticker.assert_not_called()

    def test_symbol_outside_fixed_universe_always_resolves_to_hyperliquid(self):
        self.mock_hl.get_ticker.return_value = {"symbol": "NEWCOIN", "price": 1.0}

        self.provider.get_ticker("NEWCOINUSDT")

        self.mock_hl.get_ticker.assert_called_once_with("NEWCOINUSDT")
        self.mock_binance.get_ticker.assert_not_called()
        self.mock_bybit.get_ticker.assert_not_called()

    def test_get_ohlcv_routes_and_forwards_args(self):
        df = pd.DataFrame({"close": [1.0, 2.0]})
        # BTCUSDT is index 0 -> hyperliquid per the alternating assignment.
        self.mock_hl.get_ohlcv.return_value = df

        result = self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="4h", limit=50)

        self.mock_hl.get_ohlcv.assert_called_once_with(symbol="BTCUSDT", timeframe="4h", limit=50)
        assert result is df

    def test_get_funding_open_interest_orderbook_trades_all_route_correctly(self):
        # ETHUSDT is index 1 -> binance per the alternating assignment.
        symbol = "ETHUSDT"
        assert SYMBOL_PROVIDER_ASSIGNMENT[symbol] == "binance"

        self.mock_binance.get_funding.return_value = {}
        self.mock_binance.get_open_interest.return_value = {}
        self.mock_binance.get_orderbook.return_value = {}
        self.mock_binance.get_trades.return_value = []

        self.provider.get_funding(symbol)
        self.provider.get_open_interest(symbol)
        self.provider.get_orderbook(symbol, depth=25)
        self.provider.get_trades(symbol, limit=10)

        self.mock_binance.get_funding.assert_called_once_with(symbol)
        self.mock_binance.get_open_interest.assert_called_once_with(symbol)
        self.mock_binance.get_orderbook.assert_called_once_with(symbol, depth=25)
        self.mock_binance.get_trades.assert_called_once_with(symbol, limit=10)
        self.mock_hl.get_funding.assert_not_called()


class TestMultiProviderRateLimiting:

    def test_burst_of_same_provider_calls_is_rate_limited(self):
        mock_hl = MagicMock()
        mock_hl.get_ticker.return_value = {"symbol": "BTC", "price": 1.0}
        mock_binance = MagicMock()

        # Low rate so the test can assert real wall-clock throttling without
        # a slow test: 10 req/s, burst 1 -> 5 calls must take >= ~0.32s.
        provider = MultiProvider(
            hyperliquid_provider=mock_hl,
            binance_provider=mock_binance,
            requests_per_second=10.0,
        )
        provider._hyperliquid_limiter._capacity = 1.0
        provider._hyperliquid_limiter._tokens = 1.0

        import time
        start = time.monotonic()
        for _ in range(5):
            provider.get_ticker("BTCUSDT")  # index 0 -> hyperliquid
        elapsed = time.monotonic() - start

        expected_min = 4 * (1.0 / 10.0)
        assert elapsed >= expected_min * 0.8
        assert mock_hl.get_ticker.call_count == 5
