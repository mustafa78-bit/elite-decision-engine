"""Tests for order management system."""

from decimal import Decimal

import pytest

from exchange.exceptions import ExchangeError, OrderError
from exchange.hyperliquid.connector import HyperliquidExchange
from orders.order_manager import OrderManager


class TestOrderManager:
    def test_requires_exchange(self):
        mgr = OrderManager()
        with pytest.raises(ExchangeError, match="No exchange configured"):
            mgr.create_order(symbol="BTC", side="BUY", order_type="MARKET", quantity=Decimal("0.1"))

    def test_invalid_quantity(self):
        mgr = OrderManager()
        mgr.set_exchange(HyperliquidExchange())
        with pytest.raises(OrderError, match="Invalid quantity"):
            mgr.create_order(symbol="BTC", side="BUY", order_type="MARKET", quantity=Decimal("0"))

    def test_create_and_track(self):
        mgr = OrderManager()
        mgr.set_exchange(HyperliquidExchange())
        order = mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"), price=Decimal("50000"))
        assert order.status == "FILLED"
        assert order.symbol == "BTC"

    def test_cancel_order(self):
        mgr = OrderManager()
        mgr.set_exchange(HyperliquidExchange())
        order = mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        assert mgr.cancel_order(order.id, "BTC") is True

    def test_cancel_all(self):
        mgr = OrderManager()
        mgr.set_exchange(HyperliquidExchange())
        mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        mgr.create_order(symbol="ETH", side="SELL", order_type="LIMIT", quantity=Decimal("1"))
        assert mgr.cancel_all() == 0  # already filled, not open

    def test_get_open_orders(self):
        mgr = OrderManager()
        mgr.set_exchange(HyperliquidExchange())
        order = mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        open_orders = mgr.get_open_orders()
        # Filled orders are not open
        assert len(open_orders) == 0

    def test_get_order_history(self):
        mgr = OrderManager()
        mgr.set_exchange(HyperliquidExchange())
        mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        mgr.create_order(symbol="ETH", side="SELL", order_type="MARKET", quantity=Decimal("1"))
        history = mgr.get_order_history()
        assert len(history) == 2
        btc_history = mgr.get_order_history(symbol="BTC")
        assert len(btc_history) == 1

    def test_order_status(self):
        mgr = OrderManager()
        mgr.set_exchange(HyperliquidExchange())
        order = mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        status = mgr.order_status(order.id, "BTC")
        assert status is not None
        assert status.status == "FILLED"

    def test_cancel_without_exchange(self):
        mgr = OrderManager()
        with pytest.raises(ExchangeError):
            mgr.cancel_order("test", "BTC")

    def test_cancel_all_without_exchange(self):
        mgr = OrderManager()
        with pytest.raises(ExchangeError):
            mgr.cancel_all()
