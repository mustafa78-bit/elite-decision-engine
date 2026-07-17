from typing import Any, Dict, List, Optional

from sentiment.models import SentimentScore, SentimentEvent
from sentiment.analyzer import (
    SentimentScorer,
    SentimentAggregator,
    SourceWeightManager,
)
from whale.logging import WhaleLogger

MAX_SENTIMENT_EVENTS = 10000


class SentimentIntegration:

    def __init__(self):
        self.scorer = SentimentScorer()
        self.weight_manager = SourceWeightManager()
        self.aggregator = SentimentAggregator(self.weight_manager)
        self.logger = WhaleLogger("sentiment_integration")
        self.enabled = True
        self.events: List[SentimentEvent] = []

    def process_sentiment(
        self,
        event: SentimentEvent,
        source_weight: Optional[float] = None,
    ) -> Optional[SentimentScore]:
        if not self.enabled or event is None:
            return None

        weight = source_weight if source_weight is not None else self.weight_manager.get_weight(event.source)

        score = self.scorer.score_from_sentiment(event, weight)
        self.aggregator.add_score(score)
        self.events.append(event)
        if len(self.events) > MAX_SENTIMENT_EVENTS:
            del self.events[0]

        return score

    def get_aggregated(self, asset: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"sentiment_enabled": False}
        agg = self.aggregator.aggregate(asset)
        return {
            "sentiment": agg.overall_sentiment,
            "weighted_score": agg.weighted_score,
            "confidence": agg.confidence,
            "sources": agg.sources_contributing,
        }

    def get_features(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"sentiment_enabled": False}

        assets = set(s.asset for s in self.aggregator.scores)
        agg_results = {}
        for asset in assets:
            agg = self.aggregator.aggregate(asset)
            agg_results[asset] = {
                "sentiment": agg.overall_sentiment,
                "score": agg.weighted_score,
                "confidence": agg.confidence,
                "sources": agg.sources_contributing,
            }

        bullish = sum(1 for a in agg_results.values() if a["sentiment"] == "BULLISH")
        bearish = sum(1 for a in agg_results.values() if a["sentiment"] == "BEARISH")

        features = {
            "total_scores": len(self.aggregator.scores),
            "assets_tracked": len(agg_results),
            "bullish_assets": bullish,
            "bearish_assets": bearish,
            "aggregates": agg_results,
        }

        return {
            "sentiment_enabled": True,
            "sentiment_features": features,
        }

    def get_contribution_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "asset": e.asset,
                "sentiment": e.sentiment,
                "score": e.score,
                "confidence": e.confidence,
            }
            for e in self.events[-20:]
        ]

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "sentiment_available": False}
        return {
            "ok": True,
            "sentiment_available": True,
            "features": self.get_features(),
            "events_logged": len(self.events),
        }
