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
class FearGreedIndex(SerializableMixin):
    value: float
    classification: str = "NEUTRAL"
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "macro_module"


@dataclass
class MacroEvent(SerializableMixin):
    event_id: str
    event_type: str
    asset: str
    title: str = ""
    importance: str = "MEDIUM"
    value: float = 0.0
    forecast: Optional[float] = None
    previous: Optional[float] = None
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=_utc_now)
    details: Optional[dict] = None
    source: str = "macro_module"


@dataclass
class EconomicIndicator(SerializableMixin):
    indicator_id: str
    name: str
    value: float
    country: str = "US"
    previous_value: Optional[float] = None
    forecast: Optional[float] = None
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "macro_module"


@dataclass
class VixDxySnapshot(SerializableMixin):
    vix_value: Optional[float] = None
    dxy_value: Optional[float] = None
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "macro_module"
