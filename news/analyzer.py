import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from news.models import NewsEvent
from whale.logging import WhaleLogger
from whale.timestamp import TimestampHandler


BULLISH_KEYWORDS = [
    "surge", "rally", "bullish", "breakout", "gain", "upgrade",
    "positive", "adoption", "partnership", "launch", "milestone",
    "growth", "institutional", "approval", "all-time high",
]

BEARISH_KEYWORDS = [
    "crash", "plunge", "bearish", "breakdown", "loss", "downgrade",
    "negative", "ban", "crackdown", "hack", "exploit", "fraud",
    "regulation", "sell-off", "correction", "fear",
]

MAX_FRESHNESS_HOURS = 24


class NewsClassifier:

    def __init__(self):
        self.logger = WhaleLogger("news_classifier")

    def classify_headline(self, headline: str) -> str:
        if not headline:
            return "NEUTRAL"
        lower = headline.lower()
        bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in lower)
        bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in lower)

        if bullish_count > bearish_count:
            return "BULLISH"
        elif bearish_count > bullish_count:
            return "BEARISH"
        return "NEUTRAL"

    def calculate_sentiment_score(self, headline: str) -> float:
        if not headline:
            return 0.0
        lower = headline.lower()
        bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in lower)
        bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in lower)
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        net = (bullish_count - bearish_count) / total
        return max(min(net, 1.0), -1.0)

    def calculate_confidence(
        self,
        source_reliability: float,
        headline: str,
        body_length: int = 0,
    ) -> float:
        if source_reliability is None:
            source_reliability = 0.5
        source_reliability = max(0.0, min(source_reliability, 1.0))
        base = source_reliability * 0.6
        if headline and len(headline) > 30:
            base += 0.1
        if headline and len(headline) > 60:
            base += 0.1
        if body_length > 100:
            base += 0.1
        if body_length > 500:
            base += 0.1
        return min(base, 1.0)

    def classify_event(
        self,
        event: NewsEvent,
        body_snippet: str = "",
    ) -> NewsEvent:
        if event is None:
            return event
        sentiment = self.classify_headline(event.headline)
        sentiment_score = self.calculate_sentiment_score(event.headline)
        confidence = self.calculate_confidence(
            event.source_reliability,
            event.headline,
            len(body_snippet or event.body_snippet),
        )
        event.sentiment = sentiment
        event.sentiment_score = sentiment_score
        event.confidence = round(confidence, 4)
        return event


class FreshnessValidator:

    def __init__(self, max_age_hours: int = MAX_FRESHNESS_HOURS):
        self.max_age_hours = max_age_hours
        self.logger = WhaleLogger("freshness_validator")

    def is_fresh(
        self,
        event: NewsEvent,
        max_age_hours: Optional[int] = None,
    ) -> bool:
        age = self._age_hours(event.published_at)
        threshold = max_age_hours if max_age_hours is not None else self.max_age_hours
        return age <= threshold

    def freshness_score(
        self,
        event: NewsEvent,
        max_age_hours: Optional[int] = None,
    ) -> float:
        age = self._age_hours(event.published_at)
        threshold = max_age_hours if max_age_hours is not None else self.max_age_hours
        if age <= 0 or threshold <= 0:
            return 1.0
        score = 1.0 - (age / threshold)
        return max(0.0, min(score, 1.0))

    def _age_hours(self, dt: Optional[datetime]) -> float:
        if dt is None:
            return 0.0
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = now - dt
        return max(delta.total_seconds(), 0) / 3600.0


class DuplicateDetector:

    def __init__(self):
        self.seen_headlines: List[str] = []
        self.logger = WhaleLogger("duplicate_detector")

    def normalize_headline(self, headline: str) -> str:
        if not headline:
            return ""
        lower = headline.lower().strip()
        cleaned = re.sub(r"[^a-z0-9\s]", "", lower)
        return re.sub(r"\s+", " ", cleaned).strip()

    def is_duplicate(
        self,
        event: NewsEvent,
        existing: Optional[List[NewsEvent]] = None,
    ) -> bool:
        if event is None:
            return False
        normalized = self.normalize_headline(event.headline)
        if not normalized:
            return False
        if normalized in self.seen_headlines:
            return True

        candidates = existing or []
        for other in candidates:
            if other is None or other.event_id == event.event_id:
                continue
            other_norm = self.normalize_headline(other.headline)
            if normalized == other_norm:
                return True

        return False

    def mark_seen(self, event: NewsEvent) -> None:
        normalized = self.normalize_headline(event.headline)
        if normalized not in self.seen_headlines:
            self.seen_headlines.append(normalized)

    def clear(self) -> None:
        self.seen_headlines.clear()
