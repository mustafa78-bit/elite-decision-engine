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
class SentimentScore(SerializableMixin):
    score_id: str
    asset: str
    source: str
    source_weight: float = 1.0
    sentiment: str = "NEUTRAL"
    score: float = 0.0
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=_utc_now)
    details: Optional[dict] = None
    source_name: str = "sentiment_module"


@dataclass
class AggregatedSentiment(SerializableMixin):
    asset: str
    overall_sentiment: str = "NEUTRAL"
    weighted_score: float = 0.0
    sources_contributing: int = 0
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=_utc_now)
    source: str = "sentiment_module"


@dataclass
class SentimentEvent(SerializableMixin):
    event_id: str
    event_type: str
    asset: str
    sentiment: str = "NEUTRAL"
    score: float = 0.0
    confidence: float = 0.5
    detected_at: datetime = field(default_factory=_utc_now)
    details: Optional[dict] = None
    source: str = "sentiment_module"
