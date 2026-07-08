from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from exchange.base import ExchangeAdapter
from exchange.exceptions import ExchangeError, OrderError, OrderNotFound
from exchange.models import Order

logger = logging.getLogger(__name__)


class OrderManager:
    """High-level order management system (paper mode only)."""

    def __init__(self, exchange: Optional[ExchangeAdapter] = None) -> None:
        self.exchange = exchange
        self._history: list[Order] = []
        self._open_orders: dict[str, Order] = {}

    def set_exchange(self, exchange: ExchangeAdapter) -> None:
        self.exchange = exchange

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "LIMIT",
        quantity: Optional[Decimal] = None,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        reduce_only: bool = False,
        time_in_force: str = "GTC",
        client_order_id: Optional[str] = None,
    ) -> Order:
        if self.exchange is None:
            raise ExchangeError("No exchange configured")

        if quantity is None or quantity <= Decimal("0"):
            raise OrderError("Invalid quantity")

        logger.info(
            "Creating %s %s order for %s qty=%s price=%s",
            side, order_type, symbol, quantity, price,
        )

        order = Order(
            id="",
            symbol=symbol.upper(),
            side=side.upper(),
            order_type=order_type.upper(),
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status="PENDING",
            reduce_only=reduce_only,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
        )

        filled = self.exchange.create_order(order)
        self._record_order(filled)
        return filled

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        if self.exchange is None:
            raise ExchangeError("No exchange configured")

        logger.info("Cancelling order %s for %s", order_id, symbol)
        cancelled = self.exchange.cancel_order(order_id, symbol.upper())
        if cancelled and order_id in self._open_orders:
            self._open_orders.pop(order_id)
        return cancelled

    def cancel_all(self, symbol: Optional[str] = None) -> int:
        if self.exchange is None:
            raise ExchangeError("No exchange configured")

        to_cancel = list(self._open_orders.values())
        if symbol:
            to_cancel = [o for o in to_cancel if o.symbol == symbol.upper()]

        count = 0
        for order in to_cancel:
            try:
                if self.exchange.cancel_order(order.id, order.symbol):
                    self._open_orders.pop(order.id, None)
                    count += 1
            except Exception as e:
                logger.warning("Failed to cancel order %s: %s", order.id, e)
        return count

    def order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        if self.exchange is None:
            raise ExchangeError("No exchange configured")
        return self.exchange.order_status(order_id, symbol.upper())

    def get_open_orders(self, symbol: Optional[str] = None) -> list[Order]:
        orders = list(self._open_orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol.upper()]
        return orders

    def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
    ) -> list[Order]:
        orders = list(self._history)
        if symbol:
            orders = [o for o in orders if o.symbol == symbol.upper()]
        return orders[:limit]

    def _record_order(self, order: Order) -> None:
        self._history.append(order)
        if order.status in ("PENDING", "OPEN", "PARTIALLY_FILLED"):
            self._open_orders[order.id] = order
        elif order.status in ("FILLED", "CANCELED", "REJECTED", "EXPIRED"):
            self._open_orders.pop(order.id, None)
