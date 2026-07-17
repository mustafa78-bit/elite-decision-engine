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
class NewsSource(SerializableMixin):
    source_id: str
    name: str
    domain: str = ""
    reliability_score: float = 0.5
    source_type: str = "RSS"
    is_active: bool = True
    source: str = "news_module"


@dataclass
class NewsEvent(SerializableMixin):
    event_id: str
    asset: str
    headline: str
    body_snippet: str = ""
    source_name: str = ""
    source_url: str = ""
    source_reliability: float = 0.5
    published_at: datetime = field(default_factory=_utc_now)
    detected_at: datetime = field(default_factory=_utc_now)
    sentiment: str = "NEUTRAL"
    sentiment_score: float = 0.0
    confidence: float = 0.5
    categories: List[str] = field(default_factory=list)
    is_duplicate: bool = False
    details: Optional[dict] = None
    source: str = "news_module"
