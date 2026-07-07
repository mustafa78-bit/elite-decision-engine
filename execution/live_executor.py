"""Live trading executor — validates and simulates exchange orders.

This executor NEVER sends real exchange orders. It implements the full
order lifecycle (validation, payload building, signing, sending, response
parsing) with simulated responses only.

Monitor uses the read-only HyperliquidReadOnlyAdapter to fetch real
positions and orders without ever writing to the exchange.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Protocol

from core.kill_switch import KillSwitch
from database import Trade
from execution.hyperliquid_adapter import HyperliquidReadOnlyAdapter, Position
from execution.live_order import LiveOrderStatus
from execution.order_builder import OrderBuilder
from execution.payload_validator import PayloadValidator, ValidationResult
from execution.signature_engine import SignatureEngine, SignedPayload
from execution.tp_sl import TPSLEngine


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


@dataclass(frozen=True)
class LiveMonitorResult:
    symbol: str = ""
    side: str = ""
    size: float = 0.0
    entry_price: float = 0.0
    mark_price: float = 0.0
    unrealized_pnl: float = 0.0
    liquidation_price: float = 0.0
    order_status: str = ""
    exchange_order_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


LONG_SIDE = "LONG"
SHORT_SIDE = "SHORT"
ORDER_SIDE_MAP = {"B": LONG_SIDE, "A": SHORT_SIDE}


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
    """Live order executor with read-only monitoring.

    Executes simulated orders via ExchangeAdapter and persists a
    Trade record on simulated acceptance.  Monitors open trades via
    HyperliquidReadOnlyAdapter (read-only API, no DB writes).
    """

    def __init__(
        self,
        exchange_adapter: Optional[ExchangeAdapter] = None,
        hyperliquid_adapter: Optional[HyperliquidReadOnlyAdapter] = None,
        address: str = "",
        session_factory: Optional[Callable[[], Any]] = None,
        tp_sl_engine: Optional[TPSLEngine] = None,
        order_builder: Optional[OrderBuilder] = None,
        payload_validator: Optional[PayloadValidator] = None,
        signature_engine: Optional[SignatureEngine] = None,
        kill_switch: Optional[KillSwitch] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.exchange_adapter = exchange_adapter or SimulatedExchangeAdapter()
        self.hyperliquid_adapter = hyperliquid_adapter
        self.address = address
        self.session_factory = session_factory
        self._tp_sl = tp_sl_engine or TPSLEngine()
        self._order_builder = order_builder or OrderBuilder()
        self._payload_validator = payload_validator or PayloadValidator()
        self._signature_engine = signature_engine or SignatureEngine()
        self._kill_switch = kill_switch or KillSwitch()
        self.logger = logger or logging.getLogger(__name__)

    def execute(self, candidate: Any, size: Any) -> LiveOrderResult:
        """Validate, build payload, sign, send, parse, and persist a live order."""
        if not self._kill_switch.is_running():
            state = self._kill_switch.state().value
            self.logger.warning(
                "LIVE order rejected by KillSwitch (%s): %s %s",
                state,
                getattr(candidate, "symbol", "?"),
                getattr(candidate, "side", "?"),
            )
            return LiveOrderResult(accepted=False, error=f"engine is {state}")

        self.logger.info(
            "LIVE order execution started for %s %s",
            getattr(candidate, "symbol", "?"),
            getattr(candidate, "side", "?"),
        )

        prepared = self._order_builder.build(candidate, size)
        self.logger.info("LIVE order payload built: symbol=%s qty=%s", prepared.symbol, prepared.quantity)

        validation = self._payload_validator.validate(prepared)
        if not validation.is_valid:
            error_msg = "; ".join(validation.errors)
            self.logger.error("LIVE order validation failed: %s", error_msg)
            return LiveOrderResult(accepted=False, error=error_msg)

        signed = self._signature_engine.sign(prepared)
        self.logger.debug("LIVE order payload signed")

        payload_dict = self._signed_to_dict(prepared, signed)

        exchange_response = self.exchange_adapter.place_order(payload_dict)
        self.logger.info(
            "LIVE exchange response: status=%s order_id=%s",
            exchange_response.get("status"),
            exchange_response.get("order_id"),
        )

        result = self._parse_response(exchange_response, payload_dict)
        self.logger.info(
            "LIVE order result: accepted=%s id=%s",
            result.accepted,
            result.client_order_id,
        )

        if result.accepted:
            self._persist_trade(candidate, size, result)

        return result

    def prepare_order(self, candidate: Any, size: Any) -> dict:
        self.logger.info(
            "DRY RUN: preparing order for %s %s",
            getattr(candidate, "symbol", "?"),
            getattr(candidate, "side", "?"),
        )

        prepared = self._order_builder.build(candidate, size)
        self.logger.info("DRY RUN: order built — %s %s qty=%s", prepared.symbol, prepared.side, prepared.quantity)

        validation = self._payload_validator.validate(prepared)
        if not validation.is_valid:
            self.logger.error("DRY RUN: validation failed — %s", validation.errors)
            return {
                "ready": False,
                "validated": False,
                "signed": False,
                "submitted": False,
                "errors": validation.errors,
            }

        self.logger.info("DRY RUN: payload validated successfully")

        signed = self._signature_engine.sign(prepared)
        self.logger.debug("DRY RUN: payload signed — %s", signed.signature[:20])

        self.logger.info(
            "DRY RUN complete — ready=%s validated=%s signed=%s submitted=False",
            True, True, True,
        )
        return {
            "ready": True,
            "validated": True,
            "signed": True,
            "submitted": False,
        }

    def _persist_trade(self, candidate: Any, size: Any, result: LiveOrderResult) -> None:
        """Create a Trade record from a simulated live order result."""
        if self.session_factory is None:
            self.logger.debug("No session_factory configured; Trade record not persisted")
            return

        symbol = str(getattr(candidate, "symbol", ""))
        side = str(getattr(candidate, "side", ""))
        entry = float(getattr(candidate, "entry", 0.0))
        atr = float(getattr(candidate, "scores", {}).get("atr", 0.0)) if hasattr(candidate, "scores") else 0.0
        signal_id = int(getattr(candidate, "id", 0))
        now = datetime.now(timezone.utc)

        levels = self._tp_sl.calculate(entry=entry, atr=atr, side=side)

        session = self.session_factory()
        try:
            trade = Trade(
                signal_id=signal_id,
                symbol=symbol,
                side=side,
                entry=levels["entry"],
                stop=levels["stop"],
                tp1=levels["tp1"],
                tp2=levels["tp2"],
                rr=levels["rr"],
                status="OPEN",
                exchange_order_id=result.client_order_id,
                client_order_id=result.client_order_id,
                exchange_status=LiveOrderStatus.NEW.value,
                submitted_at=now,
                updated_at=now,
                pnl=0.0,
            )
            session.add(trade)
            session.commit()
            self.logger.info(
                "Persisted live Trade %s: %s %s entry=%s",
                trade.id, symbol, side, levels["entry"],
            )
        except Exception:
            session.rollback()
            self.logger.exception("Failed to persist live Trade: %s %s", symbol, side)
        finally:
            session.close()

    def monitor_open_trades(self) -> list[LiveMonitorResult]:
        """Monitor open live trades using read-only API calls.

        Fetches positions, open orders, and current prices via the
        injected HyperliquidReadOnlyAdapter. Correlates positions
        with pending orders by coin symbol.
        """
        if self.hyperliquid_adapter is None or not self.address:
            self.logger.info("LIVE monitoring: no adapter or address configured (simulated)")
            return []

        self.logger.info("LIVE monitoring: fetching positions and orders for %s", self.address)

        try:
            positions = self.hyperliquid_adapter.get_positions(self.address)
            orders = self.hyperliquid_adapter.get_open_orders(self.address)
            prices = self.hyperliquid_adapter.get_current_prices()
        except Exception:
            self.logger.exception("LIVE monitoring failed for %s", self.address)
            return []

        results: list[LiveMonitorResult] = []

        orders_by_coin: dict[str, list] = {}
        for o in orders:
            coin = str(getattr(o, "coin", ""))
            orders_by_coin.setdefault(coin, []).append(o)

        for pos in positions:
            result = self._position_to_monitor_result(pos, orders_by_coin, prices)
            if result is not None:
                results.append(result)

        self.logger.info("LIVE monitoring: %s open positions", len(results))
        return results

    def _position_to_monitor_result(
        self,
        pos: Position,
        orders_by_coin: dict[str, list],
        prices: dict[str, float],
    ) -> Optional[LiveMonitorResult]:
        coin = str(getattr(pos, "coin", ""))
        size = abs(float(getattr(pos, "size", 0.0)))
        if size <= 0:
            return None

        side = LONG_SIDE if float(getattr(pos, "size", 0.0)) > 0 else SHORT_SIDE
        entry_price = float(getattr(pos, "entry_px", 0.0))
        mark_price = prices.get(coin, entry_price)
        unrealized_pnl = float(getattr(pos, "unrealized_pnl", 0.0))
        liquidation_price = float(getattr(pos, "liquidation_px", 0.0))

        coin_orders = orders_by_coin.get(coin, [])
        order_status = "POSITION"
        exchange_order_id = ""
        if coin_orders:
            latest = coin_orders[0]
            order_status = str(getattr(latest, "status", "open"))
            exchange_order_id = str(getattr(latest, "order_id", ""))

        return LiveMonitorResult(
            symbol=f"{coin}USDT" if not coin.endswith("USDT") else coin,
            side=side,
            size=size,
            entry_price=entry_price,
            mark_price=mark_price,
            unrealized_pnl=unrealized_pnl,
            liquidation_price=liquidation_price,
            order_status=order_status,
            exchange_order_id=exchange_order_id,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _signed_to_dict(prepared: Any, signed: Any) -> dict:
        return {
            "symbol": str(getattr(prepared, "symbol", "")),
            "side": str(getattr(prepared, "side", "")),
            "order_type": str(getattr(prepared, "order_type", "LIMIT")),
            "price": float(getattr(prepared, "price", 0.0)),
            "quantity": float(getattr(prepared, "quantity", 0.0)),
            "notional": float(getattr(prepared, "notional", 0.0)),
            "time_in_force": str(getattr(prepared, "time_in_force", "GTC")),
            "timestamp": str(getattr(prepared, "timestamp", "")),
            "signature": str(getattr(signed, "signature", "")),
            "signing_timestamp": str(getattr(signed, "signing_timestamp", "")),
            "client_order_id": str(getattr(prepared, "client_order_id", "")),
        }

    def _parse_response(self, response: dict, payload: dict) -> LiveOrderResult:
        order_id = str(response.get("order_id", uuid.uuid4()))
        status = str(response.get("status", "NEW"))
        return LiveOrderResult(
            accepted=(status != "REJECTED"),
            client_order_id=order_id,
            payload=payload,
            response=response,
        )
