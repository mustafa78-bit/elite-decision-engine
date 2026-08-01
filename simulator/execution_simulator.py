from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_SLIPPAGE_BPS = 5
DEFAULT_FEE_RATE = 0.001
DEFAULT_LATENCY_MS = (50, 200)
DEFAULT_PARTIAL_FILL_PROB = 0.05


@dataclass
class SimulationConfig:
    slippage_bps: int = DEFAULT_SLIPPAGE_BPS
    fee_rate: float = DEFAULT_FEE_RATE
    latency_ms_min: int = DEFAULT_LATENCY_MS[0]
    latency_ms_max: int = DEFAULT_LATENCY_MS[1]
    partial_fill_probability: float = DEFAULT_PARTIAL_FILL_PROB
    partial_fill_min_pct: float = 0.1
    partial_fill_max_pct: float = 0.9


@dataclass
class FillResult:
    order_id: str
    symbol: str
    side: str
    requested_quantity: Decimal
    filled_quantity: Decimal
    requested_price: Optional[Decimal]
    fill_price: Decimal
    slippage: Decimal
    fee: Decimal
    latency_ms: int
    partial: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionSimulator:
    """Simulates real-market execution conditions for paper trades.

    Models slippage, fees, latency, and partial fills.
    """

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config = config or SimulationConfig()

    def simulate_fill(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        market_price: Optional[Decimal] = None,
    ) -> FillResult:
        """Simulate order execution with realistic market conditions."""

        # Latency
        latency = random.randint(self.config.latency_ms_min, self.config.latency_ms_max)

        # Slippage
        if price is not None:
            slippage_mult = Decimal(str(self.config.slippage_bps)) / Decimal("10000")
            if side.upper() == "BUY":
                fill_price = price * (Decimal("1") + slippage_mult)
            else:
                fill_price = price * (Decimal("1") - slippage_mult)
        elif market_price is not None:
            fill_price = market_price
        else:
            fill_price = Decimal("0")

        slippage = fill_price - (price or fill_price)

        # Partial fill
        partial = random.random() < self.config.partial_fill_probability
        if partial:
            fill_pct = Decimal(
                str(
                    random.uniform(
                        self.config.partial_fill_min_pct,
                        self.config.partial_fill_max_pct,
                    )
                )
            )
            filled_qty = (quantity * fill_pct).quantize(Decimal("0.00001"))
        else:
            filled_qty = quantity

        # Fee
        notional = filled_qty * fill_price
        fee = (notional * Decimal(str(self.config.fee_rate))).quantize(Decimal("0.01"))

        return FillResult(
            order_id=order_id,
            symbol=symbol,
            side=side,
            requested_quantity=quantity,
            filled_quantity=filled_qty,
            requested_price=price,
            fill_price=fill_price.quantize(Decimal("0.01")),
            slippage=slippage.quantize(Decimal("0.01")),
            fee=fee,
            latency_ms=latency,
            partial=partial,
        )

    def calculate_net_pnl(
        self,
        entry_fill: FillResult,
        exit_fill: FillResult,
    ) -> Decimal:
        """Calculate net PnL after fees for a round-trip trade."""
        entry_cost = entry_fill.filled_quantity * entry_fill.fill_price
        exit_value = exit_fill.filled_quantity * exit_fill.fill_price
        gross_pnl = exit_value - entry_cost

        # LONG: exit_value - entry_cost, SHORT: entry_cost - exit_value
        if exit_fill.side.upper() == "SELL":
            gross_pnl = exit_value - entry_cost
        else:
            gross_pnl = entry_cost - exit_value

        total_fees = entry_fill.fee + exit_fill.fee
        return (gross_pnl - total_fees).quantize(Decimal("0.01"))

    def report(self, fill: FillResult) -> str:
        """Return a human-readable summary of the fill."""
        return (
            f"Order {fill.order_id} | {fill.side} {fill.filled_quantity} {fill.symbol} "
            f"@ ${fill.fill_price} | slippage=${fill.slippage} fee=${fill.fee} "
            f"latency={fill.latency_ms}ms {'PARTIAL' if fill.partial else 'FULL'}"
        )
