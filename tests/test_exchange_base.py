"""Tests for exchange adapter layer."""

from decimal import Decimal

from exchange.base import ExchangeAdapter
from exchange.exceptions import (
    AuthenticationError,
    ExchangeConnectionError,
    ExchangeError,
    ExchangeTimeoutError,
    InsufficientFunds,
    InvalidOrder,
    MarketDataError,
    OrderError,
    OrderNotFound,
    PositionNotFound,
    RateLimitError,
    SymbolNotFound,
)
from exchange.models import Balance, Candle, Order, Position, Ticker


class TestExchangeModels:
    def test_order_defaults(self):
        o = Order(id="1", symbol="BTC", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        assert o.status == "PENDING"
        assert o.filled_quantity == Decimal("0")
        assert o.time_in_force == "GTC"
        assert o.reduce_only is False

    def test_position_defaults(self):
        p = Position(symbol="BTC", side="LONG", quantity=Decimal("0.1"), entry_price=Decimal("50000"), current_price=Decimal("51000"))
        assert p.unrealized_pnl == Decimal("0")
        assert p.leverage == 1
        assert p.liquidation_price is None

    def test_balance_defaults(self):
        b = Balance(currency="USDT", total=Decimal("10000"), available=Decimal("8000"))
        assert b.locked == Decimal("0")
        assert b.wallet == "SPOT"

    def test_ticker_fields(self):
        t = Ticker(symbol="BTC", bid=Decimal("50000"), ask=Decimal("50001"), last=Decimal("50000.5"), volume_24h=Decimal("1000"), high_24h=Decimal("51000"), low_24h=Decimal("49000"), change_24h=Decimal("2.5"))
        assert t.symbol == "BTC"
        assert t.bid == Decimal("50000")

    def test_candle_fields(self):
        from datetime import datetime, timezone
        c = Candle(symbol="BTC", timeframe="1h", open=Decimal("100"), high=Decimal("110"), low=Decimal("90"), close=Decimal("105"), volume=Decimal("1000"), timestamp=datetime.now(timezone.utc))
        assert c.closed is True
        assert c.timeframe == "1h"


class TestExchangeExceptions:
    def test_exception_hierarchy(self):
        assert issubclass(ExchangeConnectionError, ExchangeError)
        assert issubclass(AuthenticationError, ExchangeError)
        assert issubclass(RateLimitError, ExchangeError)
        assert issubclass(OrderError, ExchangeError)
        assert issubclass(InsufficientFunds, OrderError)
        assert issubclass(InvalidOrder, OrderError)
        assert issubclass(OrderNotFound, OrderError)
        assert issubclass(PositionNotFound, ExchangeError)
        assert issubclass(SymbolNotFound, ExchangeError)
        assert issubclass(MarketDataError, ExchangeError)
        assert issubclass(ExchangeTimeoutError, ExchangeError)

    def test_exception_messages(self):
        try:
            raise InsufficientFunds("Not enough USDT")
        except OrderError as e:
            assert "Not enough USDT" in str(e)

    def test_generic_catch(self):
        for exc_cls in [ExchangeConnectionError, AuthenticationError, RateLimitError, OrderNotFound, PositionNotFound, SymbolNotFound, MarketDataError, ExchangeTimeoutError]:
            try:
                raise exc_cls("test")
            except ExchangeError:
                pass


class TestExchangeInterface:
    def test_interface_has_abstract_methods(self):
        import abc
        methods = [
            "ticker", "candles", "account_balance", "positions",
            "create_order", "cancel_order", "order_status", "order_history",
            "trading_enabled",
        ]
        abstract_methods = getattr(ExchangeAdapter, "__abstractmethods__", frozenset())
        for name in methods:
            assert name in abstract_methods, f"{name} should be abstract"
