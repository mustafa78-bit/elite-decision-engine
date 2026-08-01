from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Order:
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: str = "PENDING"
    filled_quantity: Decimal = Decimal("0")
    avg_fill_price: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    client_order_id: Optional[str] = None
    reduce_only: bool = False
    time_in_force: str = "GTC"


@dataclass(frozen=True)
class Position:
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    leverage: int = 1
    liquidation_price: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class Balance:
    currency: str
    total: Decimal
    available: Decimal
    locked: Decimal = Decimal("0")
    wallet: str = "SPOT"
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Ticker:
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    change_24h: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timestamp: datetime
    closed: bool = True
