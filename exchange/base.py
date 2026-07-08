from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from exchange.models import Balance, Candle, Order, Position, Ticker


class ExchangeAdapter(ABC):
    """Abstract base for exchange connectors."""

    name: str

    @abstractmethod
    def ticker(self, symbol: str) -> Ticker:
        ...

    @abstractmethod
    def candles(
        self, symbol: str, timeframe: str = "1h", limit: int = 200
    ) -> list[Candle]:
        ...

    @abstractmethod
    def account_balance(self) -> list[Balance]:
        ...

    @abstractmethod
    def positions(self, symbol: Optional[str] = None) -> list[Position]:
        ...

    @abstractmethod
    def create_order(self, order: Order) -> Order:
        ...

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        ...

    @abstractmethod
    def order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        ...

    @abstractmethod
    def order_history(
        self, symbol: str, limit: int = 50
    ) -> list[Order]:
        ...

    @abstractmethod
    def trading_enabled(self) -> bool:
        ...
