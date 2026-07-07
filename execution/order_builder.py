from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class PreparedOrder:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float
    reduce_only: bool
    time_in_force: str
    client_order_id: str
    timestamp: str
    notional: float = 0.0
    trailing: dict = field(default_factory=dict)


class OrderBuilder:

    def build(
        self,
        candidate: Any,
        size: Any,
        order_type: str = "LIMIT",
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> PreparedOrder:
        symbol = str(getattr(candidate, "symbol", ""))
        side = str(getattr(candidate, "side", ""))
        entry = float(getattr(candidate, "entry", 0.0))
        quantity = float(getattr(size, "quantity", 0.0))
        notional = float(getattr(size, "notional_value", 0.0))

        return PreparedOrder(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=entry,
            reduce_only=reduce_only,
            time_in_force=time_in_force,
            client_order_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            notional=notional,
        )
