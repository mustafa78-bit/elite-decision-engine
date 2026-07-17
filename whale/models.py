from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


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
class WhaleEvent(SerializableMixin):
    event_id: str
    wallet_address: str
    event_type: str
    asset: str
    value_usd: float
    confidence: float
    detected_at: datetime
    source: str = "whale_module"
    details: Optional[dict] = None


@dataclass
class WalletActivity(SerializableMixin):
    wallet_address: str
    total_volume_usd: float = 0.0
    transfer_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    reputation_score: float = 50.0
    behavior_type: str = "UNKNOWN"


@dataclass
class TransferEvent(SerializableMixin):
    tx_id: str
    from_address: str
    to_address: str
    asset: str
    amount: float
    value_usd: float
    timestamp: datetime
    direction: str = "UNKNOWN"
    confidence: float = 0.5
    is_large: bool = False
    is_suspicious: bool = False
    detected_at: datetime = field(default_factory=_utc_now)
