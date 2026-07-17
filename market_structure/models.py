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
class PriceCandle(SerializableMixin):
    asset: str
    high: float
    low: float
    open: float
    close: float
    volume: float = 0.0
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "market_structure_module"


@dataclass
class SwingPoint(SerializableMixin):
    point_id: str
    asset: str
    point_type: str
    price: float
    timestamp: datetime = field(default_factory=_utc_now)
    index: int = 0
    strength: float = 0.5
    source: str = "market_structure_module"


@dataclass
class StructureBreak(SerializableMixin):
    break_id: str
    asset: str
    break_type: str
    direction: str
    price: float
    previous_swing_price: float = 0.0
    timestamp: datetime = field(default_factory=_utc_now)
    confidence: float = 0.5
    source: str = "market_structure_module"


@dataclass
class TrendState(SerializableMixin):
    asset: str
    trend: str = "NEUTRAL"
    strength: float = 0.0
    swing_highs: List[float] = field(default_factory=list)
    swing_lows: List[float] = field(default_factory=list)
    last_update: datetime = field(default_factory=_utc_now)
    source: str = "market_structure_module"


@dataclass
class MarketStructureEvent(SerializableMixin):
    event_id: str
    event_type: str
    asset: str
    price: float = 0.0
    confidence: float = 0.5
    detected_at: datetime = field(default_factory=_utc_now)
    details: Optional[dict] = None
    source: str = "market_structure_module"
