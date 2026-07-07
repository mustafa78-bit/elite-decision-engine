"""Deterministic unit tests for PayloadValidator and ValidationResult.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

from dataclasses import dataclass

from execution.payload_validator import PayloadValidator, ValidationResult


@dataclass(frozen=True)
class _ValidOrder:
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    order_type: str = "LIMIT"
    quantity: float = 1.0
    price: float = 50000.0
    timestamp: str = "2026-07-07T12:00:00+00:00"


class TestValidationResult:

    def test_valid_result(self):
        r = ValidationResult(is_valid=True)
        assert r.is_valid is True
        assert r.errors == []

    def test_invalid_result(self):
        r = ValidationResult(is_valid=False, errors=["bad"])
        assert r.is_valid is False
        assert r.errors == ["bad"]

    def test_frozen(self):
        import pytest
        r = ValidationResult(is_valid=True)
        with pytest.raises(AttributeError):
            r.is_valid = False


class TestPayloadValidator:

    def test_valid_order_passes(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder())
        assert result.is_valid is True
        assert result.errors == []

    def test_empty_symbol(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(symbol=""))
        assert result.is_valid is False
        assert any("symbol" in e for e in result.errors)

    def test_missing_symbol(self):
        validator = PayloadValidator()

        @dataclass(frozen=True)
        class _NoSymbol:
            side: str = "LONG"
            order_type: str = "LIMIT"
            quantity: float = 1.0
            price: float = 50000.0
            timestamp: str = "2026-01-01T00:00:00+00:00"

        result = validator.validate(_NoSymbol())
        assert result.is_valid is False

    def test_invalid_side(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(side="INVALID"))
        assert result.is_valid is False
        assert any("side" in e for e in result.errors)

    def test_short_side_valid(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(side="SHORT"))
        assert result.is_valid is True

    def test_zero_quantity(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(quantity=0.0))
        assert result.is_valid is False
        assert any("quantity" in e for e in result.errors)

    def test_negative_quantity(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(quantity=-1.0))
        assert result.is_valid is False

    def test_zero_price(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(price=0.0))
        assert result.is_valid is False
        assert any("price" in e for e in result.errors)

    def test_negative_price(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(price=-100.0))
        assert result.is_valid is False

    def test_missing_timestamp(self):
        validator = PayloadValidator()

        @dataclass(frozen=True)
        class _NoTimestamp:
            symbol: str = "BTCUSDT"
            side: str = "LONG"
            order_type: str = "LIMIT"
            quantity: float = 1.0
            price: float = 50000.0

        result = validator.validate(_NoTimestamp())
        assert result.is_valid is False
        assert any("timestamp" in e for e in result.errors)

    def test_bad_timestamp_format(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(timestamp="not-a-timestamp"))
        assert result.is_valid is False
        assert any("timestamp" in e for e in result.errors)

    def test_naive_timestamp_rejected(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(timestamp="2026-01-01T00:00:00"))
        assert result.is_valid is False
        assert any("timezone-aware" in e for e in result.errors)

    def test_invalid_order_type(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(order_type="INVALID"))
        assert result.is_valid is False
        assert any("order_type" in e for e in result.errors)

    def test_market_order_type_valid(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(order_type="MARKET"))
        assert result.is_valid is True

    def test_accumulates_multiple_errors(self):
        validator = PayloadValidator()
        result = validator.validate(_ValidOrder(symbol="", side="BAD", quantity=0.0, price=0.0, timestamp=""))
        assert result.is_valid is False
        assert len(result.errors) >= 4
