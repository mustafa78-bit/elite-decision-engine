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
class Trade(SerializableMixin):
    trade_id: str
    asset: str
    side: str
    size: float
    price: float
    timestamp: datetime = field(default_factory=_utc_now)
    is_aggressive: bool = False
    source: str = "orderflow_module"


@dataclass
class DeltaPoint(SerializableMixin):
    asset: str
    timestamp: datetime = field(default_factory=_utc_now)
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    delta: float = 0.0
    cumulative_delta: float = 0.0
    source: str = "orderflow_module"


@dataclass
class VolumeImbalance(SerializableMixin):
    asset: str
    timeframe: str = "1m"
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    ratio: float = 1.0
    direction: str = "NEUTRAL"
    strength: float = 0.0
    source: str = "orderflow_module"


@dataclass
class CVD(SerializableMixin):
    asset: str
    value: float = 0.0
    trend: str = "NEUTRAL"
    timestamp: datetime = field(default_factory=_utc_now)
    divergence: Optional[str] = None
    source: str = "orderflow_module"


@dataclass
class AggressiveOrder(SerializableMixin):
    order_id: str
    asset: str
    side: str
    size: float
    price: float
    timestamp: datetime = field(default_factory=_utc_now)
    is_aggressive: bool = True
    confidence: float = 0.5
    source: str = "orderflow_module"


@dataclass
class AbsorptionSignal(SerializableMixin):
    asset: str
    direction: str
    strength: float = 0.0
    confidence: float = 0.5
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "orderflow_module"


@dataclass
class ExhaustionSignal(SerializableMixin):
    asset: str
    direction: str
    strength: float = 0.0
    confidence: float = 0.5
    price_change: float = 0.0
    volume_drop: float = 0.0
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "orderflow_module"


@dataclass
class OrderFlowEvent(SerializableMixin):
    event_id: str
    event_type: str
    asset: str
    value: float = 0.0
    confidence: float = 0.5
    detected_at: datetime = field(default_factory=_utc_now)
    details: Optional[dict] = None
    source: str = "orderflow_module"
