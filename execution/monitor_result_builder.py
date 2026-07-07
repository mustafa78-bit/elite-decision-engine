from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from execution.hyperliquid_adapter import Position


LONG_SIDE = "LONG"
SHORT_SIDE = "SHORT"
ORDER_SIDE_MAP = {"B": LONG_SIDE, "A": SHORT_SIDE}


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


class MonitorResultBuilder:

    def build(
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
