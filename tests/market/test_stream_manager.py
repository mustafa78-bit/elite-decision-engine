"""Unit tests for MarketStreamManager and the market.stream shared singletons."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from market.stream.cache import CandleStreamCache, get_shared_candle_stream_cache
from market.stream.manager import MarketStreamManager, get_shared_stream_manager


class TestMarketStreamManagerRouting:

    def test_symbols_route_to_the_client_matching_their_provider_assignment(self):
        from config import SYMBOL_PROVIDER_ASSIGNMENT

        # BTCUSDT/ETHUSDT/SOLUSDT (indices 0/1/2) resolve to
        # hyperliquid/binance/bybit respectively per the real i%5 formula --
        # confirm that hasn't silently changed before relying on it below.
        assert SYMBOL_PROVIDER_ASSIGNMENT["BTCUSDT"] == "hyperliquid"
        assert SYMBOL_PROVIDER_ASSIGNMENT["ETHUSDT"] == "binance"
        assert SYMBOL_PROVIDER_ASSIGNMENT["SOLUSDT"] == "bybit"

        cache = CandleStreamCache()
        manager = MarketStreamManager(
            cache=cache,
            symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            timeframes=["1h"],
        )

        assert manager.hyperliquid.get_subscriptions() == [("BTC", "1h")]
        assert manager.binance.get_subscriptions() == [("ETHUSDT", "1h")]
        assert manager.bybit.get_subscriptions() == [("SOLUSDT", "1h")]

    def test_symbol_outside_assignment_table_defaults_to_hyperliquid(self):
        cache = CandleStreamCache()
        manager = MarketStreamManager(cache=cache, symbols=["NEWCOINUSDT"], timeframes=["1h"])

        assert manager.binance.get_subscriptions() == []
        assert manager.bybit.get_subscriptions() == []
        assert manager.hyperliquid.get_subscriptions() != []

    def test_all_three_clients_share_the_same_cache_instance(self):
        cache = CandleStreamCache()
        manager = MarketStreamManager(cache=cache, symbols=["BTCUSDT"], timeframes=["1h"])

        assert manager.binance.cache is cache
        assert manager.bybit.cache is cache
        assert manager.hyperliquid.cache is cache


class TestMarketStreamManagerLifecycle:

    def setup_method(self):
        self.mock_binance = MagicMock()
        self.mock_binance.start = AsyncMock()
        self.mock_binance.stop = AsyncMock()
        self.mock_binance.is_running = True
        self.mock_binance.is_connected = True

        self.mock_bybit = MagicMock()
        self.mock_bybit.start = AsyncMock()
        self.mock_bybit.stop = AsyncMock()
        self.mock_bybit.is_running = True
        self.mock_bybit.is_connected = True

        self.mock_hl = MagicMock()
        self.mock_hl.start = AsyncMock()
        self.mock_hl.stop = AsyncMock()
        self.mock_hl.is_running = True
        self.mock_hl.is_connected = True

        self.manager = MarketStreamManager(
            cache=CandleStreamCache(),
            symbols=["BTCUSDT"],
            timeframes=["1h"],
            binance_client=self.mock_binance,
            bybit_client=self.mock_bybit,
            hyperliquid_client=self.mock_hl,
        )

    @pytest.mark.asyncio
    async def test_start_all_starts_every_client(self):
        await self.manager.start_all()
        self.mock_binance.start.assert_called_once()
        self.mock_bybit.start.assert_called_once()
        self.mock_hl.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_all_stops_every_client(self):
        await self.manager.stop_all()
        self.mock_binance.stop.assert_called_once()
        self.mock_bybit.stop.assert_called_once()
        self.mock_hl.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_one_client_failing_to_start_does_not_block_the_others(self):
        self.mock_bybit.start.side_effect = Exception("bybit connection refused")

        await self.manager.start_all()

        self.mock_binance.start.assert_called_once()
        self.mock_bybit.start.assert_called_once()
        self.mock_hl.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_one_client_failing_to_stop_does_not_block_the_others(self):
        self.mock_binance.stop.side_effect = Exception("close error")

        await self.manager.stop_all()

        self.mock_binance.stop.assert_called_once()
        self.mock_bybit.stop.assert_called_once()
        self.mock_hl.stop.assert_called_once()

    def test_status_reports_each_clients_running_and_connected_state(self):
        status = self.manager.status
        assert status == {
            "binance": {"running": True, "connected": True},
            "bybit": {"running": True, "connected": True},
            "hyperliquid": {"running": True, "connected": True},
        }


class TestSharedCandleStreamCache:

    def setup_method(self):
        import market.stream.cache as cache_module
        cache_module._shared_cache_instance = None

    def teardown_method(self):
        import market.stream.cache as cache_module
        cache_module._shared_cache_instance = None

    def test_returns_a_candle_stream_cache_instance(self):
        assert isinstance(get_shared_candle_stream_cache(), CandleStreamCache)

    def test_returns_the_same_instance_on_repeated_calls(self):
        assert get_shared_candle_stream_cache() is get_shared_candle_stream_cache()


class TestSharedStreamManager:

    def setup_method(self):
        import market.stream.manager as manager_module
        manager_module._shared_manager_instance = None

    def teardown_method(self):
        import market.stream.manager as manager_module
        manager_module._shared_manager_instance = None

    def test_returns_a_market_stream_manager_instance(self):
        assert isinstance(get_shared_stream_manager(), MarketStreamManager)

    def test_returns_the_same_instance_on_repeated_calls(self):
        assert get_shared_stream_manager() is get_shared_stream_manager()
