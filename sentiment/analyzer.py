from typing import Dict, List, Optional

from sentiment.models import SentimentScore, AggregatedSentiment, SentimentEvent
from whale.logging import WhaleLogger

MAX_SCORES = 10000

BULLISH_THRESHOLD = 0.2
BEARISH_THRESHOLD = -0.2


class SentimentScorer:

    def __init__(self):
        self.logger = WhaleLogger("sentiment_scorer")

    def classify_score(self, score: float) -> str:
        if score > BULLISH_THRESHOLD:
            return "BULLISH"
        elif score < BEARISH_THRESHOLD:
            return "BEARISH"
        return "NEUTRAL"

    def calculate_confidence(self, score: float, source_weight: float) -> float:
        abs_score = min(abs(score), 1.0)
        base = (abs_score * 0.5) + (source_weight * 0.5)
        return min(base, 1.0)

    def score_from_sentiment(
        self,
        event: SentimentEvent,
        source_weight: float = 1.0,
    ) -> SentimentScore:
        if event.sentiment == "BULLISH":
            score = 0.6
        elif event.sentiment == "BEARISH":
            score = -0.6
        else:
            score = 0.0

        score += event.score

        classified = self.classify_score(score)
        confidence = self.calculate_confidence(score, source_weight)

        return SentimentScore(
            score_id=f"ss_{event.asset}_{event.event_id}",
            asset=event.asset,
            source=event.source,
            source_weight=source_weight,
            sentiment=classified,
            score=round(max(min(score, 1.0), -1.0), 4),
            confidence=round(confidence, 4),
            details=event.details,
        )


class SourceWeightManager:

    def __init__(self):
        self.weights: Dict[str, float] = {}
        self.logger = WhaleLogger("source_weight_manager")

    def get_weight(self, source: str, default: float = 1.0) -> float:
        return self.weights.get(source, default)

    def set_weight(self, source: str, weight: float) -> None:
        self.weights[source] = max(0.0, min(weight, 1.0))

    def adjust_weight(
        self,
        source: str,
        accuracy: float,
        adjustment_factor: float = 0.1,
    ) -> float:
        current = self.get_weight(source)
        delta = (accuracy - 0.5) * adjustment_factor
        new_weight = current + delta
        new_weight = max(0.0, min(new_weight, 1.0))
        self.weights[source] = round(new_weight, 4)
        return self.weights[source]

    def reset(self, source: Optional[str] = None) -> None:
        if source:
            self.weights.pop(source, None)
        else:
            self.weights.clear()


class SentimentAggregator:

    def __init__(self, weight_manager: Optional[SourceWeightManager] = None):
        self.scores: List[SentimentScore] = []
        self.events: List[SentimentEvent] = []
        self.weight_manager = weight_manager or SourceWeightManager()
        self.logger = WhaleLogger("sentiment_aggregator")

    def add_score(self, score: SentimentScore) -> AggregatedSentiment:
        self.scores.append(score)
        if len(self.scores) > MAX_SCORES:
            del self.scores[0]
        return self.aggregate(score.asset)

    def aggregate(self, asset: str) -> AggregatedSentiment:
        relevant = [s for s in self.scores if s.asset == asset]
        if not relevant:
            return AggregatedSentiment(asset=asset)

        total_weight = 0.0
        weighted_sum = 0.0
        total_confidence = 0.0

        for s in relevant:
            w = s.source_weight
            weighted_sum += s.score * w
            total_weight += w
            total_confidence += s.confidence * w

        if total_weight == 0:
            return AggregatedSentiment(asset=asset)

        avg_score = weighted_sum / total_weight
        avg_confidence = total_confidence / total_weight

        if avg_score > BULLISH_THRESHOLD:
            sentiment = "BULLISH"
        elif avg_score < BEARISH_THRESHOLD:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"

        result = AggregatedSentiment(
            asset=asset,
            overall_sentiment=sentiment,
            weighted_score=round(avg_score, 4),
            sources_contributing=len(relevant),
            confidence=round(avg_confidence, 4),
        )

        self.events.append(SentimentEvent(
            event_id=f"agg_{asset}_{int(__import__('time').time())}",
            event_type="AGGREGATED_SENTIMENT",
            asset=asset,
            sentiment=sentiment,
            score=round(avg_score, 4),
            confidence=round(avg_confidence, 4),
            details={"sources": len(relevant), "weighted_score": round(avg_score, 4)},
        ))
        if len(self.events) > MAX_SCORES:
            del self.events[0]

        return result

    def get_recent(self, asset: Optional[str] = None, limit: int = 20) -> List[AggregatedSentiment]:
        results = [
            self.aggregate(asset)
            for asset in set(s.asset for s in self.scores)
        ]
        if asset:
            results = [r for r in results if r.asset == asset]
        return results[-limit:]
