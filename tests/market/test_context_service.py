"""Tests for ContextService."""

from unittest.mock import MagicMock
import pandas as pd

from market.context import ContextService


class TestContextService:

    def setup_method(self):
        self.mock_provider = MagicMock()
        self.mock_cache = MagicMock()
        self.mock_cache.make_key.return_value = "test_key"
        self.service = ContextService(provider=self.mock_provider, cache=self.mock_cache)

    def test_get_btc_context_empty(self):
        self.mock_cache.get.return_value = None
        self.mock_provider.get_ohlcv.return_value = pd.DataFrame()
        ctx = self.service.get_btc_context()
        assert ctx.get("available") is False
        assert ctx["btc_price"] == 0.0

    def test_get_btc_context_with_data(self):
        self.mock_cache.get.return_value = None
        df = pd.DataFrame({"close": [50000.0, 51000.0, 51500.0]})
        self.mock_provider.get_ohlcv.return_value = df
        ctx = self.service.get_btc_context()
        assert ctx["available"] is True
        assert ctx["btc_price"] == 51500.0

    def test_get_market_session_returns_string(self):
        session = self.service.get_market_session()
        assert session in ("ASIAN", "LONDON", "NY", "CLOSED")

    def test_get_funding_state_neutral(self):
        self.mock_provider.get_funding.return_value = {"rate": 0.0001}
        state = self.service.get_funding_state("BTC")
        assert state["state"] == "NEUTRAL"

    def test_get_funding_state_high_long(self):
        self.mock_provider.get_funding.return_value = {"rate": 0.02}
        state = self.service.get_funding_state("BTC")
        assert state["state"] == "HIGH_LONG"

    def test_get_funding_state_high_short(self):
        self.mock_provider.get_funding.return_value = {"rate": -0.02}
        state = self.service.get_funding_state("BTC")
        assert state["state"] == "HIGH_SHORT"
