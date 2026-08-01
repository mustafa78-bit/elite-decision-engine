"""Tests for Hyperliquid exchange connector."""

from decimal import Decimal

import pytest

from exchange.exceptions import MarketDataError
from exchange.hyperliquid.connector import HyperliquidExchange
from exchange.models import Order


class TestHyperliquidExchange:
    def test_implements_adapter(self):
        ex = HyperliquidExchange()
        assert ex.name == "hyperliquid"
        assert ex.trading_enabled() is True

    def test_account_balance(self):
        ex = HyperliquidExchange()
        balances = ex.account_balance()
        assert len(balances) >= 1
        assert balances[0].currency == "USDT"

    def test_create_order_paper(self):
        ex = HyperliquidExchange()
        order = Order(id="", symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"), price=Decimal("50000"))
        filled = ex.create_order(order)
        assert filled.status == "FILLED"
        assert filled.filled_quantity == Decimal("0.1")

    def test_cancel_order(self):
        ex = HyperliquidExchange()
        order = Order(id="", symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        filled = ex.create_order(order)
        assert ex.cancel_order(filled.id, "BTC") is True

    def test_cancel_nonexistent(self):
        ex = HyperliquidExchange()
        assert ex.cancel_order("nonexistent", "BTC") is False

    def test_order_status(self):
        ex = HyperliquidExchange()
        order = Order(id="", symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        filled = ex.create_order(order)
        result = ex.order_status(filled.id, "BTC")
        assert result is not None
        assert result.status == "FILLED"

    def test_order_status_nonexistent(self):
        ex = HyperliquidExchange()
        assert ex.order_status("nonexistent", "BTC") is None

    def test_order_history(self):
        ex = HyperliquidExchange()
        o1 = Order(id="", symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        o2 = Order(id="", symbol="ETH", side="SELL", order_type="MARKET", quantity=Decimal("1"))
        ex.create_order(o1)
        ex.create_order(o2)
        btc_history = ex.order_history("BTC")
        assert len(btc_history) == 1
        eth_history = ex.order_history("ETH")
        assert len(eth_history) == 1

    def test_ticker_raises_on_bad_symbol(self):
        ex = HyperliquidExchange()
        from exchange.exceptions import ExchangeConnectionError
        with pytest.raises((MarketDataError, ExchangeConnectionError)):
            ex.ticker("NONEXISTENT_COIN_12345")

    def test_candles_raises_on_bad_symbol(self):
        ex = HyperliquidExchange()
        from exchange.exceptions import ExchangeConnectionError
        with pytest.raises((MarketDataError, ExchangeConnectionError)):
            ex.candles("NONEXISTENT_COIN_12345")
