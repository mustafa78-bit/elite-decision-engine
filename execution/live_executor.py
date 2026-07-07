"""Live trading executor — validates and simulates exchange orders.

This executor NEVER sends real exchange orders. It implements the full
order lifecycle (validation, payload building, signing, sending, response
parsing) with simulated responses only.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Protocol


@dataclass(frozen=True)
class LiveOrderRequest:
    symbol: str
    side: str
    order_type: str = "LIMIT"
    price: float = 0.0
    quantity: float = 0.0
    notional: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reduce_only: bool = False
    time_in_force: str = "GTC"


@dataclass(frozen=True)
class LiveOrderResult:
    accepted: bool
    mode: str = "LIVE"
    exchange: str = "Hyperliquid"
    client_order_id: str = ""
    payload: dict = field(default_factory=dict)
    response: dict = field(default_factory=dict)
    error: Optional[str] = None


class ExchangeAdapter(Protocol):
    """Interface for exchange communication."""

    def place_order(self, payload: dict) -> dict:
        ...

    def cancel_order(self, order_id: str) -> dict:
        ...

    def get_order_status(self, order_id: str) -> dict:
        ...


class SimulatedExchangeAdapter:
    """Returns canned responses. Never calls a real exchange."""

    def place_order(self, payload: dict) -> dict:
        return {
            "order_id": str(uuid.uuid4()),
            "status": "NEW",
            "filled": 0.0,
        }

    def cancel_order(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "CANCELED"}

    def get_order_status(self, order_id: str) -> dict:
        return {
            "order_id": order_id,
            "status": "FILLED",
            "filled": 0.0,
        }


class LiveExecutor:
    """Simulated live order executor.

    Validates, builds, and logs order requests but never sends real orders.
    """

    def __init__(
        self,
        exchange_adapter: Optional[ExchangeAdapter] = None,
        session_factory: Optional[Callable[[], Any]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.exchange_adapter = exchange_adapter or SimulatedExchangeAdapter()
        self.session_factory = session_factory
        self.logger = logger or logging.getLogger(__name__)

    def execute(self, candidate: Any, size: Any) -> LiveOrderResult:
        """Validate, build payload, sign, send, and parse a live order."""
        self.logger.info(
            "LIVE order execution started for %s %s",
            getattr(candidate, "symbol", "?"),
            getattr(candidate, "side", "?"),
        )

        validation_error = self._validate(candidate, size)
        if validation_error:
            self.logger.error("LIVE order validation failed: %s", validation_error)
            return LiveOrderResult(accepted=False, error=validation_error)

        payload = self._build_payload(candidate, size)
        self.logger.info("LIVE order payload built: symbol=%s qty=%s", payload.get("symbol"), payload.get("quantity"))

        signed_payload = self._sign_payload(payload)
        self.logger.debug("LIVE order payload signed")

        exchange_response = self.exchange_adapter.place_order(signed_payload)
        self.logger.info(
            "LIVE exchange response: status=%s order_id=%s",
            exchange_response.get("status"),
            exchange_response.get("order_id"),
        )

        result = self._parse_response(exchange_response, payload)
        self.logger.info(
            "LIVE order result: accepted=%s id=%s",
            result.accepted,
            result.client_order_id,
        )
        return result

    def monitor_open_trades(self) -> list[LiveOrderResult]:
        """Simulate monitoring open live trades."""
        self.logger.info("LIVE monitoring: no open trades (simulated)")
        return []

    def _validate(self, candidate: Any, size: Any) -> Optional[str]:
        if candidate is None or size is None:
            return "candidate and size are required"
        symbol = getattr(candidate, "symbol", None)
        side = getattr(candidate, "side", None)
        entry = getattr(candidate, "entry", None)
        quantity = getattr(size, "quantity", None)
        if not symbol:
            return "symbol is required"
        if side not in ("LONG", "SHORT"):
            return "side must be LONG or SHORT"
        if not entry or entry <= 0:
            return "entry must be greater than zero"
        if not quantity or quantity <= 0:
            return "quantity must be greater than zero"
        return None

    def _build_payload(self, candidate: Any, size: Any) -> dict:
        return {
            "symbol": str(getattr(candidate, "symbol", "")),
            "side": str(getattr(candidate, "side", "")),
            "order_type": "LIMIT",
            "price": float(getattr(candidate, "entry", 0.0)),
            "quantity": float(getattr(size, "quantity", 0.0)),
            "notional": float(getattr(size, "notional_value", 0.0)),
            "time_in_force": "GTC",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _sign_payload(self, payload: dict) -> dict:
        signed = dict(payload)
        signed["signature"] = "SIMULATED_SIGNATURE_PLACEHOLDER"
        signed["signing_timestamp"] = datetime.now(timezone.utc).isoformat()
        return signed

    def _parse_response(self, response: dict, payload: dict) -> LiveOrderResult:
        order_id = str(response.get("order_id", uuid.uuid4()))
        status = str(response.get("status", "NEW"))
        return LiveOrderResult(
            accepted=(status != "REJECTED"),
            client_order_id=order_id,
            payload=payload,
            response=response,
        )
