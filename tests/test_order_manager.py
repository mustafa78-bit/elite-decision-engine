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

    def test_cancel_order_updates_history_status(self):
        class MockExchange(HyperliquidExchange):
            def create_order(self, order):
                import dataclasses
                # Keep it PENDING so it stays in open orders and is recorded with PENDING status
                filled = dataclasses.replace(order, id="mock_1", status="PENDING")
                self._orders["mock_1"] = filled
                return filled

        mgr = OrderManager()
        mgr.set_exchange(MockExchange())
        order = mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        assert order.status == "PENDING"

        # Verify it is in history and open orders as PENDING
        assert len(mgr.get_open_orders()) == 1
        history = mgr.get_order_history()
        assert len(history) == 1
        assert history[0].status == "PENDING"

        # Cancel the order
        assert mgr.cancel_order(order.id, "BTC") is True

        # Now verify it is removed from open orders but status is CANCELED in history
        assert len(mgr.get_open_orders()) == 0
        history_after = mgr.get_order_history()
        assert len(history_after) == 1
        assert history_after[0].status == "CANCELED"

    def test_cancel_all_updates_history_status(self):
        class MockExchange(HyperliquidExchange):
            def create_order(self, order):
                import dataclasses
                order_id = f"mock_{self._next_order_id}"
                self._next_order_id += 1
                filled = dataclasses.replace(order, id=order_id, status="PENDING")
                self._orders[order_id] = filled
                return filled

        mgr = OrderManager()
        mgr.set_exchange(MockExchange())
        order1 = mgr.create_order(symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        order2 = mgr.create_order(symbol="ETH", side="SELL", order_type="LIMIT", quantity=Decimal("1"))

        assert order1.id == "mock_1"
        assert order2.id == "mock_2"
        assert len(mgr.get_open_orders()) == 2
        history = mgr.get_order_history()
        assert len(history) == 2
        assert history[0].status == "PENDING"
        assert history[1].status == "PENDING"

        # Cancel all
        assert mgr.cancel_all() == 2

        # Verify open orders are empty, and history is updated to CANCELED
        assert len(mgr.get_open_orders()) == 0
        history_after = mgr.get_order_history()
        assert len(history_after) == 2
        assert history_after[0].status == "CANCELED"
        assert history_after[1].status == "CANCELED"

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
        assert order.symbol == "BTC"
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
