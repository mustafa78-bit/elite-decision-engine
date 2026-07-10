"""Tests for IndicatorService."""

from unittest.mock import MagicMock
import pandas as pd

from market.indicators import IndicatorService


class TestIndicatorService:

    def setup_method(self):
        self.service = IndicatorService()

    def test_get_indicators_with_empty_df(self):
        result = self.service.get_indicators("BTC", "1h", pd.DataFrame())
        assert result == {}

    def test_get_indicators_with_none_df(self):
        result = self.service.get_indicators("BTC", "1h", None)
        assert result == {}

    def test_get_indicator_values_filters_numeric(self):
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_cache.make_key.return_value = "test"
        service = IndicatorService(cache=mock_cache)

        # Mock the indicator engine to return mixed values
        service._indicators.calculate = MagicMock(return_value={
            "ema20": 100.0, "ema50": 101.0, "rsi": 55,
            "atr": 500, "entry": 100.5,
        })
        service._volatility.score = MagicMock(return_value={"volatility": 0.01, "score": 0.3})
        service._volume.score = MagicMock(return_value={"score": 0.7})

        df = pd.DataFrame({"close": [100.0, 101.0]})
        result = service.get_indicator_values("BTC", "1h", df)
        assert all(isinstance(v, (int, float)) for v in result.values())

    def test_caching(self):
        mock_cache = MagicMock()
        mock_cache.make_key.return_value = "indicators:BTC:1h"
        service = IndicatorService(cache=mock_cache)

        # First call: cache miss
        mock_cache.get.return_value = None
        service._indicators.calculate = MagicMock(return_value={"ema20": 100.0})
        service._volatility.score = MagicMock(return_value={"volatility": 0.01, "score": 0.3})
        service._volume.score = MagicMock(return_value={"score": 0.7})

        df = pd.DataFrame({"close": [100.0, 101.0]})
        result1 = service.get_indicators("BTC", "1h", df)

        # Second call: cache hit
        mock_cache.get.return_value = {"ema20": 100.0, "cached": True}
        result2 = service.get_indicators("BTC", "1h", pd.DataFrame({"close": [200.0]}))
        assert result2.get("cached") is True
