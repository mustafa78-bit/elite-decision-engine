"""Deterministic unit tests for OrderBuilder and PreparedOrder.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from execution.order_builder import OrderBuilder, PreparedOrder


@dataclass(frozen=True)
class _MockCandidate:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    entry: float = 50000.0
    scores: dict = None
    confidence: float = 0.9
    decision: str = "APPROVE"
    signal: Any = None

    def __post_init__(self):
        if self.scores is None:
            object.__setattr__(self, "scores", {"atr": 500.0})


@dataclass(frozen=True)
class _MockSize:
    quantity: float = 1.0
    notional_value: float = 50000.0
    risk_amount: float = 750.0


class TestPreparedOrder:

    def test_dataclass_fields(self):
        order = PreparedOrder(
            symbol="BTCUSDT",
            side="LONG",
            order_type="LIMIT",
            quantity=1.0,
            price=50000.0,
            reduce_only=False,
            time_in_force="GTC",
            client_order_id="oid-123",
            timestamp="2026-01-01T00:00:00+00:00",
        )
        assert order.symbol == "BTCUSDT"
        assert order.side == "LONG"
        assert order.order_type == "LIMIT"
        assert order.quantity == 1.0
        assert order.price == 50000.0
        assert order.reduce_only is False
        assert order.time_in_force == "GTC"
        assert order.client_order_id == "oid-123"
        assert order.timestamp == "2026-01-01T00:00:00+00:00"

    def test_frozen(self):
        order = PreparedOrder(
            symbol="BTCUSDT", side="LONG", order_type="LIMIT",
            quantity=1.0, price=50000.0, reduce_only=False,
            time_in_force="GTC", client_order_id="oid-1", timestamp="now",
        )
        import pytest
        with pytest.raises(AttributeError):
            order.symbol = "ETHUSDT"


class TestOrderBuilder:

    def test_build_returns_prepared_order(self):
        builder = OrderBuilder()
        order = builder.build(_MockCandidate(), _MockSize())
        assert isinstance(order, PreparedOrder)
        assert order.symbol == "BTCUSDT"
        assert order.side == "LONG"
        assert order.order_type == "LIMIT"
        assert order.quantity == 1.0
        assert order.price == 50000.0

    def test_build_generates_client_order_id(self):
        builder = OrderBuilder()
        order1 = builder.build(_MockCandidate(), _MockSize())
        order2 = builder.build(_MockCandidate(), _MockSize())
        assert order1.client_order_id != order2.client_order_id

    def test_build_timestamp_is_iso_format(self):
        builder = OrderBuilder()
        order = builder.build(_MockCandidate(), _MockSize())
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(order.timestamp)
        assert dt.tzinfo is not None

    def test_build_with_notional(self):
        builder = OrderBuilder()
        order = builder.build(_MockCandidate(), _MockSize())
        assert order.notional == 50000.0

    def test_build_reduce_only_default_false(self):
        builder = OrderBuilder()
        order = builder.build(_MockCandidate(), _MockSize())
        assert order.reduce_only is False

    def test_build_time_in_force_default_gtc(self):
        builder = OrderBuilder()
        order = builder.build(_MockCandidate(), _MockSize())
        assert order.time_in_force == "GTC"

    def test_build_short_side(self):
        candidate = _MockCandidate(side="SHORT", entry=3000.0)
        size = _MockSize(quantity=2.0, notional_value=6000.0, risk_amount=90.0)
        builder = OrderBuilder()
        order = builder.build(candidate, size)
        assert order.side == "SHORT"
        assert order.price == 3000.0
        assert order.quantity == 2.0
