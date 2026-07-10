"""Tests for MarketDataService."""

from unittest.mock import MagicMock
import pandas as pd

from market.services import MarketDataService


class TestMarketDataService:

    def setup_method(self):
        self.mock_provider = MagicMock()
        self.mock_cache = MagicMock()
        self.mock_cache.make_key.return_value = "test_key"
        self.mock_indicators = MagicMock()
        self.mock_features = MagicMock()
        self.mock_context = MagicMock()

        self.service = MarketDataService(
            provider=self.mock_provider,
            cache=self.mock_cache,
            indicators=self.mock_indicators,
            features=self.mock_features,
            context=self.mock_context,
        )

    def test_get_ohlcv_cache_hit(self):
        df = pd.DataFrame({"close": [100.0]})
        self.mock_cache.get.return_value = df
        result = self.service.get_ohlcv("BTC")
        assert result is df
        self.mock_provider.get_ohlcv.assert_not_called()

    def test_get_ohlcv_cache_miss(self):
        df = pd.DataFrame({"close": [100.0]})
        self.mock_cache.get.return_value = None
        self.mock_provider.get_ohlcv.return_value = df
        result = self.service.get_ohlcv("BTC")
        self.mock_provider.get_ohlcv.assert_called_once()

    def test_get_asset_empty_ohlcv(self):
        self.mock_cache.get.return_value = None
        self.mock_provider.get_ohlcv.return_value = pd.DataFrame()
        asset = self.service.get_asset("BTC")
        assert asset.symbol == "BTC"
        assert asset.is_empty

    def test_get_asset_with_data(self):
        self.mock_cache.get.return_value = None
        df = pd.DataFrame({"close": [100.0, 101.0, 102.0]})
        self.mock_provider.get_ohlcv.return_value = df
        self.mock_indicators.get_indicators.return_value = {"ema20": 101.0}
        self.mock_features.extract.return_value = {"trend": "BULLISH"}
        self.mock_context.get_context.return_value = {"session": "NY"}

        asset = self.service.get_asset("ETH")
        assert asset.symbol == "ETH"
        assert asset.price == 102.0
        assert asset.indicators["ema20"] == 101.0
        assert asset.features["trend"] == "BULLISH"
        assert asset.context["session"] == "NY"

    def test_get_price(self):
        self.mock_cache.get.return_value = None
        df = pd.DataFrame({"close": [100.0, 105.0]})
        self.mock_provider.get_ohlcv.return_value = df
        self.mock_indicators.get_indicators.return_value = {}
        self.mock_features.extract.return_value = {}
        self.mock_context.get_context.return_value = {}

        price = self.service.get_price("BTC")
        assert price == 105.0

    def test_invalidate_asset(self):
        self.service.invalidate_asset("BTC")
        assert self.mock_cache.invalidate.call_count == 2

    def test_invalidate_all(self):
        self.service.invalidate_all()
        self.mock_cache.clear.assert_called_once()
