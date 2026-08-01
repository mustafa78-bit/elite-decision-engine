"""Tests for Binance exchange connector."""

from decimal import Decimal

import pytest

from exchange.binance.connector import BinanceExchange
from exchange.exceptions import (
    AuthenticationError,
    ExchangeConnectionError,
    MarketDataError,
)
from exchange.models import Order


class TestBinanceExchange:
    def test_implements_adapter(self):
        ex = BinanceExchange()
        assert ex.name == "binance"
        assert ex.trading_enabled() is True

    def test_account_balance_paper(self):
        ex = BinanceExchange()
        balances = ex.account_balance()
        assert len(balances) >= 1
        assert balances[0].currency == "USDT"

    def test_ticker_fails_without_network(self):
        ex = BinanceExchange(timeout=1)
        with pytest.raises((MarketDataError, ExchangeConnectionError)):
            ex.ticker("THISISFAKE123")

    def test_candles_fails_without_network(self):
        ex = BinanceExchange(timeout=1)
        with pytest.raises((MarketDataError, ExchangeConnectionError)):
            ex.candles("THISISFAKE123")

    def test_create_order_paper(self):
        ex = BinanceExchange()
        order = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"), price=Decimal("50000"))
        filled = ex.create_order(order)
        assert filled.status == "FILLED"
        assert filled.filled_quantity == Decimal("0.1")

    def test_cancel_order(self):
        ex = BinanceExchange()
        order = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        filled = ex.create_order(order)
        assert ex.cancel_order(filled.id, "BTCUSDT") is True

    def test_cancel_nonexistent(self):
        ex = BinanceExchange()
        assert ex.cancel_order("nonexistent", "BTCUSDT") is False

    def test_order_status(self):
        ex = BinanceExchange()
        order = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        filled = ex.create_order(order)
        result = ex.order_status(filled.id, "BTCUSDT")
        assert result is not None
        assert result.status == "FILLED"

    def test_order_status_nonexistent(self):
        ex = BinanceExchange()
        assert ex.order_status("nonexistent", "BTCUSDT") is None

    def test_order_history(self):
        ex = BinanceExchange()
        o1 = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        o2 = Order(id="", symbol="ETHUSDT", side="SELL", order_type="MARKET", quantity=Decimal("1"))
        ex.create_order(o1)
        ex.create_order(o2)
        assert len(ex.order_history("BTCUSDT")) == 1
        assert len(ex.order_history("ETHUSDT")) == 1

    def test_authenticated_requests_fail_without_secret(self):
        ex = BinanceExchange(api_key="test_key")
        with pytest.raises(AuthenticationError):
            ex._signed_request("GET", "/api/v3/account")
