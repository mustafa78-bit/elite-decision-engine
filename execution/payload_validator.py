from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


VALID_SIDES = frozenset({"LONG", "SHORT"})
VALID_ORDER_TYPES = frozenset({"LIMIT", "MARKET", "STOP_LIMIT", "STOP_MARKET"})
VALID_TIME_IN_FORCE = frozenset({"GTC", "IOC", "FOK", "POST_ONLY"})


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


class PayloadValidator:

    def validate(self, order: Any) -> ValidationResult:
        errors: list[str] = []

        symbol = getattr(order, "symbol", None)
        side = getattr(order, "side", None)
        order_type = getattr(order, "order_type", None)
        quantity = getattr(order, "quantity", None)
        price = getattr(order, "price", None)
        timestamp = getattr(order, "timestamp", None)

        if not symbol or not str(symbol).strip():
            errors.append("symbol is required")

        if side not in VALID_SIDES:
            errors.append(f"side must be one of {sorted(VALID_SIDES)}, got '{side}'")

        if order_type not in VALID_ORDER_TYPES:
            errors.append(f"order_type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'")

        if quantity is None or quantity <= 0:
            errors.append(f"quantity must be greater than zero, got {quantity}")

        if price is None or price <= 0:
            errors.append(f"price must be greater than zero, got {price}")

        if not timestamp:
            errors.append("timestamp is required")
        else:
            self._validate_timestamp(timestamp, errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    @staticmethod
    def _validate_timestamp(timestamp: str, errors: list[str]) -> None:
        try:
            dt = datetime.fromisoformat(timestamp)
            if dt.tzinfo is None:
                errors.append("timestamp must be timezone-aware")
        except (ValueError, TypeError):
            errors.append(f"timestamp is not valid ISO-8601: '{timestamp}'")
