from datetime import datetime, timezone

from sentiment.models import SentimentScore, AggregatedSentiment, SentimentEvent
from sentiment.analyzer import SentimentScorer, SentimentAggregator, SourceWeightManager
from sentiment.integration import SentimentIntegration


class TestSentimentModels:

    def test_sentiment_score_defaults(self):
        ss = SentimentScore(score_id="s1", asset="BTC", source="news")
        assert ss.sentiment == "NEUTRAL"
        assert ss.score == 0.0
        assert ss.confidence == 0.5
        assert ss.source_weight == 1.0

    def test_sentiment_score_custom(self):
        ss = SentimentScore(
            score_id="s2", asset="ETH", source="twitter",
            sentiment="BULLISH", score=0.8, confidence=0.9,
        )
        assert ss.sentiment == "BULLISH"
        assert ss.score == 0.8

    def test_aggregated_sentiment_defaults(self):
        ag = AggregatedSentiment(asset="BTC")
        assert ag.overall_sentiment == "NEUTRAL"
        assert ag.weighted_score == 0.0
        assert ag.sources_contributing == 0

    def test_sentiment_event_defaults(self):
        se = SentimentEvent(event_id="e1", event_type="SOCIAL_BUZZ", asset="BTC")
        assert se.sentiment == "NEUTRAL"
        assert se.source == "sentiment_module"

    def test_serialization(self):
        ss = SentimentScore(score_id="s1", asset="BTC", source="news", score=0.5)
        d = ss.to_dict()
        assert d["score_id"] == "s1"
        assert d["score"] == 0.5


class TestSentimentScorer:

    def test_classify_bullish(self):
        scorer = SentimentScorer()
        assert scorer.classify_score(0.5) == "BULLISH"
        assert scorer.classify_score(0.21) == "BULLISH"

    def test_classify_bearish(self):
        scorer = SentimentScorer()
        assert scorer.classify_score(-0.5) == "BEARISH"
        assert scorer.classify_score(-0.21) == "BEARISH"

    def test_classify_neutral(self):
        scorer = SentimentScorer()
        assert scorer.classify_score(0.0) == "NEUTRAL"
        assert scorer.classify_score(0.19) == "NEUTRAL"
        assert scorer.classify_score(-0.19) == "NEUTRAL"

    def test_calculate_confidence_high(self):
        scorer = SentimentScorer()
        conf = scorer.calculate_confidence(0.8, 1.0)
        assert conf > 0.7
        assert conf <= 1.0

    def test_calculate_confidence_low(self):
        scorer = SentimentScorer()
        conf = scorer.calculate_confidence(0.0, 0.0)
        assert conf == 0.0

    def test_score_from_bullish_event(self):
        scorer = SentimentScorer()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH")
        score = scorer.score_from_sentiment(event)
        assert score.sentiment == "BULLISH"
        assert score.score > 0.0

    def test_score_from_bearish_event(self):
        scorer = SentimentScorer()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BEARISH")
        score = scorer.score_from_sentiment(event)
        assert score.sentiment == "BEARISH"
        assert score.score < 0.0

    def test_score_from_neutral_event(self):
        scorer = SentimentScorer()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="NEUTRAL")
        score = scorer.score_from_sentiment(event)
        assert score.sentiment == "NEUTRAL"

    def test_score_clamped(self):
        scorer = SentimentScorer()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH", score=10.0)
        score = scorer.score_from_sentiment(event)
        assert score.score <= 1.0

    def test_score_from_sentiment_with_details(self):
        scorer = SentimentScorer()
        event = SentimentEvent(
            event_id="e1", event_type="NEWS", asset="BTC",
            sentiment="BULLISH", details={"source": "twitter"},
        )
        score = scorer.score_from_sentiment(event, source_weight=0.8)
        assert score.details == {"source": "twitter"}
        assert score.source_weight == 0.8


class TestSourceWeightManager:

    def test_get_weight_default(self):
        swm = SourceWeightManager()
        assert swm.get_weight("unknown") == 1.0

    def test_set_and_get(self):
        swm = SourceWeightManager()
        swm.set_weight("twitter", 0.5)
        assert swm.get_weight("twitter") == 0.5

    def test_set_weight_clamped(self):
        swm = SourceWeightManager()
        swm.set_weight("twitter", 2.0)
        assert swm.get_weight("twitter") == 1.0
        swm.set_weight("twitter", -1.0)
        assert swm.get_weight("twitter") == 0.0

    def test_adjust_weight_up(self):
        swm = SourceWeightManager()
        swm.set_weight("twitter", 0.5)
        result = swm.adjust_weight("twitter", 0.8)
        assert result > 0.5

    def test_adjust_weight_down(self):
        swm = SourceWeightManager()
        swm.set_weight("twitter", 0.5)
        result = swm.adjust_weight("twitter", 0.2)
        assert result < 0.5

    def test_reset_specific(self):
        swm = SourceWeightManager()
        swm.set_weight("twitter", 0.5)
        swm.set_weight("news", 0.8)
        swm.reset("twitter")
        assert swm.get_weight("twitter") == 1.0
        assert swm.get_weight("news") == 0.8

    def test_reset_all(self):
        swm = SourceWeightManager()
        swm.set_weight("twitter", 0.5)
        swm.reset()
        assert swm.get_weight("twitter") == 1.0


class TestSentimentAggregator:

    def test_aggregate_empty(self):
        agg = SentimentAggregator()
        result = agg.aggregate("BTC")
        assert result.overall_sentiment == "NEUTRAL"
        assert result.sources_contributing == 0

    def test_aggregate_bullish(self):
        agg = SentimentAggregator()
        s1 = SentimentScore(score_id="s1", asset="BTC", source="news", score=0.6, sentiment="BULLISH")
        s2 = SentimentScore(score_id="s2", asset="BTC", source="twitter", score=0.4, sentiment="BULLISH")
        agg.add_score(s1)
        result = agg.add_score(s2)
        assert result.overall_sentiment == "BULLISH"
        assert result.weighted_score > 0.3

    def test_aggregate_bearish(self):
        agg = SentimentAggregator()
        s1 = SentimentScore(score_id="s3", asset="ETH", source="news", score=-0.7, sentiment="BEARISH")
        result = agg.add_score(s1)
        assert result.overall_sentiment == "BEARISH"
        assert result.weighted_score < -0.5

    def test_aggregate_neutral(self):
        agg = SentimentAggregator()
        s1 = SentimentScore(score_id="s4", asset="BTC", source="news", score=0.1, sentiment="NEUTRAL")
        result = agg.add_score(s1)
        assert result.overall_sentiment == "NEUTRAL"

    def test_aggregate_weighted(self):
        agg = SentimentAggregator()
        s1 = SentimentScore(score_id="s1", asset="BTC", source="news", score=0.8, source_weight=2.0)
        s2 = SentimentScore(score_id="s2", asset="BTC", source="twitter", score=-0.5, source_weight=0.5)
        agg.add_score(s1)
        result = agg.add_score(s2)
        assert result.overall_sentiment == "BULLISH"

    def test_get_recent(self):
        agg = SentimentAggregator()
        s1 = SentimentScore(score_id="s1", asset="BTC", source="news", score=0.5)
        agg.add_score(s1)
        recent = agg.get_recent("BTC")
        assert len(recent) == 1
        assert recent[0].asset == "BTC"

    def test_create_events_on_aggregate(self):
        agg = SentimentAggregator()
        s1 = SentimentScore(score_id="s1", asset="BTC", source="news", score=0.5)
        agg.add_score(s1)
        assert len(agg.events) == 1
        assert agg.events[0].event_type == "AGGREGATED_SENTIMENT"


class TestSentimentIntegration:

    def test_enabled_default(self):
        si = SentimentIntegration()
        assert si.enabled is True

    def test_process_sentiment_returns_score(self):
        si = SentimentIntegration()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH")
        score = si.process_sentiment(event)
        assert score is not None
        assert score.sentiment == "BULLISH"

    def test_process_sentiment_disabled(self):
        si = SentimentIntegration()
        si.enabled = False
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH")
        result = si.process_sentiment(event)
        assert result is None

    def test_process_sentiment_with_weight(self):
        si = SentimentIntegration()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH")
        score = si.process_sentiment(event, source_weight=0.7)
        assert score.source_weight == 0.7

    def test_get_aggregated(self):
        si = SentimentIntegration()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH")
        si.process_sentiment(event)
        agg = si.get_aggregated("BTC")
        assert agg["sentiment"] == "BULLISH"

    def test_get_aggregated_disabled(self):
        si = SentimentIntegration()
        si.enabled = False
        agg = si.get_aggregated("BTC")
        assert agg["sentiment_enabled"] is False

    def test_get_features_enabled(self):
        si = SentimentIntegration()
        features = si.get_features()
        assert features["sentiment_enabled"] is True
        assert "sentiment_features" in features

    def test_get_features_disabled(self):
        si = SentimentIntegration()
        si.enabled = False
        features = si.get_features()
        assert features["sentiment_enabled"] is False

    def test_get_features_tracks_scores(self):
        si = SentimentIntegration()
        si.process_sentiment(SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH"))
        si.process_sentiment(SentimentEvent(event_id="e2", event_type="NEWS", asset="ETH", sentiment="BEARISH"))
        features = si.get_features()
        sf = features["sentiment_features"]
        assert sf["total_scores"] == 2
        assert sf["assets_tracked"] == 2

    def test_get_contribution_log(self):
        si = SentimentIntegration()
        event = SentimentEvent(event_id="e1", event_type="NEWS", asset="BTC", sentiment="BULLISH")
        si.process_sentiment(event)
        log = si.get_contribution_log()
        assert len(log) == 1
        assert log[0]["event_id"] == "e1"

    def test_evaluate_enabled(self):
        si = SentimentIntegration()
        result = si.evaluate()
        assert result["ok"] is True
        assert result["sentiment_available"] is True

    def test_evaluate_disabled(self):
        si = SentimentIntegration()
        si.enabled = False
        result = si.evaluate()
        assert result["ok"] is True
        assert result["sentiment_available"] is False
