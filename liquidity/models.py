from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SerializableMixin:

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key in self.__dataclass_fields__:
            value = getattr(self, key)
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list):
                result[key] = [
                    v.to_dict() if hasattr(v, "to_dict") else v for v in value
                ]
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result


@dataclass
class LiquidityZone(SerializableMixin):
    zone_id: str
    asset: str
    zone_type: str
    price_low: float
    price_high: float
    strength: float = 0.5
    touches: int = 0
    formed_at: datetime = field(default_factory=_utc_now)
    last_tested: Optional[datetime] = None
    is_active: bool = True
    source: str = "liquidity_module"


@dataclass
class LiquiditySweep(SerializableMixin):
    sweep_id: str
    asset: str
    zone_id: str
    direction: str
    price: float
    volume: float
    timestamp: datetime = field(default_factory=_utc_now)
    confidence: float = 0.5
    source: str = "liquidity_module"


@dataclass
class RestingLiquidity(SerializableMixin):
    asset: str
    side: str
    price: float
    size: float
    order_count: int = 0
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "liquidity_module"


@dataclass
class LiquidityImbalance(SerializableMixin):
    asset: str
    bid_volume: float
    ask_volume: float
    ratio: float = 1.0
    direction: str = "NEUTRAL"
    timestamp: datetime = field(default_factory=_utc_now)
    strength: float = 0.0
    source: str = "liquidity_module"


@dataclass
class LiquiditySweep(SerializableMixin):
    sweep_id: str
    asset: str
    zone_id: str
    direction: str
    price: float
    volume: float
    timestamp: datetime = field(default_factory=_utc_now)
    confidence: float = 0.5
    details: Optional[dict] = None
    source: str = "liquidity_module"


@dataclass
class LiquidityEvent(SerializableMixin):
    event_id: str
    event_type: str
    asset: str
    price: float
    volume: float = 0.0
    confidence: float = 0.5
    detected_at: datetime = field(default_factory=_utc_now)
    details: Optional[dict] = None
    source: str = "liquidity_module"
