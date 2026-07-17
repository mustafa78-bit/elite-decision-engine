from typing import Any, Dict, List, Optional

from news.models import NewsEvent, NewsSource
from news.analyzer import NewsClassifier, FreshnessValidator, DuplicateDetector
from whale.logging import WhaleLogger

MAX_NEWS_EVENTS = 10000


class NewsIntegration:

    def __init__(self):
        self.classifier = NewsClassifier()
        self.freshness = FreshnessValidator()
        self.dedup = DuplicateDetector()
        self.logger = WhaleLogger("news_integration")
        self.enabled = True
        self.events: List[NewsEvent] = []
        self.sources: Dict[str, NewsSource] = {}

    def register_source(self, source: NewsSource) -> None:
        if source is None:
            return
        self.sources[source.source_id] = source

    def process_news(
        self,
        event: NewsEvent,
        body_snippet: str = "",
    ) -> Optional[NewsEvent]:
        if not self.enabled or event is None:
            return None

        if self.dedup.is_duplicate(event, self.events):
            event.is_duplicate = True
            return event

        classified = self.classifier.classify_event(event, body_snippet)
        self.dedup.mark_seen(classified)
        self.events.append(classified)
        if len(self.events) > MAX_NEWS_EVENTS:
            del self.events[0]
        return classified

    def get_features(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"news_enabled": False}

        fresh = [e for e in self.events if self.freshness.is_fresh(e)]
        bullish = [e for e in fresh if e.sentiment == "BULLISH" and e.confidence > 0.5]
        bearish = [e for e in fresh if e.sentiment == "BEARISH" and e.confidence > 0.5]
        neutral = [e for e in fresh if e.sentiment == "NEUTRAL"]
        high_conf = [e for e in fresh if e.confidence > 0.7]

        features = {
            "total_events": len(self.events),
            "fresh_events": len(fresh),
            "bullish_count": len(bullish),
            "bearish_count": len(bearish),
            "neutral_count": len(neutral),
            "high_confidence_count": len(high_conf),
            "active_sources": len(self.sources),
        }

        if bullish or bearish:
            features["dominant_sentiment"] = (
                "BULLISH" if len(bullish) >= len(bearish) else "BEARISH"
            )
        else:
            features["dominant_sentiment"] = "NEUTRAL"

        return {
            "news_enabled": True,
            "news_features": features,
        }

    def get_contribution_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "asset": e.asset,
                "sentiment": e.sentiment,
                "confidence": e.confidence,
                "is_duplicate": e.is_duplicate,
            }
            for e in self.events[-20:]
        ]

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "news_available": False}
        return {
            "ok": True,
            "news_available": True,
            "features": self.get_features(),
            "events_logged": len(self.events),
        }
