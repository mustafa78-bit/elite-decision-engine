"""Tests for MultiProvider's routing + rate-limiting."""

from unittest.mock import MagicMock

import pandas as pd

from config import FIXED_COIN_UNIVERSE, SYMBOL_PROVIDER_ASSIGNMENT
from market.provider.multi import MultiProvider, get_shared_multi_provider


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

    def test_mkr_and_ton_are_overridden_off_their_delisted_halted_exchange(self):
        # MKRUSDT: Bybit's linear perp is delisted (confirmed live
        # 2026-08-20). TONUSDT: Binance's pair is halted (status=BREAK).
        # Both route to Hyperliquid instead of their formulaic assignment.
        assert SYMBOL_PROVIDER_ASSIGNMENT["MKRUSDT"] == "hyperliquid"
        assert SYMBOL_PROVIDER_ASSIGNMENT["TONUSDT"] == "hyperliquid"


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
        # A copy, not the same object -- see TestMultiProviderOhlcvCache below
        # for why (every cache hit must get its own DataFrame, not one every
        # caller shares and could mutate).
        assert result is not df
        pd.testing.assert_frame_equal(result, df)

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


class TestMultiProviderOhlcvCache:
    """A single ChartPanel render fetches the same symbol/timeframe's OHLCV
    via /market/live AND separately re-triggers a server-side OHLCV fetch
    for each of /market/levels, /market/divergence, /market/channel,
    /market/liquidity-zones, /market/volume-profile -- 6 near-simultaneous
    fetches of what's actually one dataset. Confirmed live 2026-08-21 as a
    real, meaningful contributor to Hyperliquid rate-limit pressure."""

    def setup_method(self):
        self.mock_hl = MagicMock()
        self.mock_binance = MagicMock()
        self.mock_bybit = MagicMock()
        self.provider = MultiProvider(
            hyperliquid_provider=self.mock_hl,
            binance_provider=self.mock_binance,
            bybit_provider=self.mock_bybit,
            requests_per_second=1000.0,
        )

    def test_identical_calls_within_ttl_hit_the_cache(self):
        df = pd.DataFrame({"close": [1.0, 2.0]})
        self.mock_hl.get_ohlcv.return_value = df

        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)
        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)
        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)

        self.mock_hl.get_ohlcv.assert_called_once_with(symbol="BTCUSDT", timeframe="1h", limit=100)

    def test_different_symbol_timeframe_or_limit_bypasses_the_cache(self):
        self.mock_hl.get_ohlcv.return_value = pd.DataFrame({"close": [1.0]})
        self.mock_binance.get_ohlcv.return_value = pd.DataFrame({"close": [2.0]})

        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)
        # ETHUSDT routes to a different provider entirely (binance) --
        # exercises that the cache key is scoped correctly, not just that
        # it varies by symbol.
        self.provider.get_ohlcv(symbol="ETHUSDT", timeframe="1h", limit=100)
        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="4h", limit=100)  # different timeframe
        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=50)  # different limit

        assert self.mock_hl.get_ohlcv.call_count == 3
        assert self.mock_binance.get_ohlcv.call_count == 1

    def test_cache_entry_expires_after_ttl(self, monkeypatch):
        # Shrinks the TTL itself rather than faking time.monotonic() --
        # multi.py's own TokenBucketRateLimiter also reads the real,
        # global time.monotonic() for its token refill math, so freezing
        # it here would desync the limiter's internal bookkeeping (it seeds
        # _last_refill from the real clock at construction time, before
        # this test's monkeypatch takes effect) and hang the test in a
        # real, very long time.sleep() inside acquire().
        import time as time_module

        import market.provider.multi as multi_module
        monkeypatch.setattr(multi_module, "_OHLCV_CACHE_TTL_SECONDS", 0.01)

        self.mock_hl.get_ohlcv.return_value = pd.DataFrame({"close": [1.0]})

        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)
        time_module.sleep(0.02)
        self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)

        assert self.mock_hl.get_ohlcv.call_count == 2

    def test_returned_dataframes_are_independent_copies(self):
        df = pd.DataFrame({"close": [1.0, 2.0]})
        self.mock_hl.get_ohlcv.return_value = df

        first = self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)
        second = self.provider.get_ohlcv(symbol="BTCUSDT", timeframe="1h", limit=100)

        first.loc[0, "close"] = 999.0
        assert second.loc[0, "close"] == 1.0


class TestSharedMultiProvider:

    def setup_method(self):
        # get_shared_multi_provider() caches into a module-level global --
        # reset it so each test starts from a clean, unconstructed state
        # rather than leaking whatever a previous test (or import-time
        # caller) already built.
        import market.provider.multi as multi_module
        multi_module._shared_instance = None

    def teardown_method(self):
        import market.provider.multi as multi_module
        multi_module._shared_instance = None

    def test_returns_a_multi_provider_instance(self):
        instance = get_shared_multi_provider()
        assert isinstance(instance, MultiProvider)

    def test_returns_the_same_instance_on_repeated_calls(self):
        first = get_shared_multi_provider()
        second = get_shared_multi_provider()
        assert first is second

    def test_concurrent_first_calls_all_get_the_same_instance(self):
        import threading

        results: list[MultiProvider] = []
        results_lock = threading.Lock()

        def worker():
            instance = get_shared_multi_provider()
            with results_lock:
                results.append(instance)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        assert all(r is results[0] for r in results)
