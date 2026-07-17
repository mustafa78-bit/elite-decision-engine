from datetime import datetime, timedelta, timezone

from news.models import NewsSource, NewsEvent
from news.analyzer import NewsClassifier, FreshnessValidator, DuplicateDetector
from news.integration import NewsIntegration


class TestNewsModels:

    def test_news_source_defaults(self):
        ns = NewsSource(source_id="s1", name="CoinDesk")
        assert ns.source_type == "RSS"
        assert ns.reliability_score == 0.5
        assert ns.is_active is True
        assert ns.source == "news_module"

    def test_news_source_custom(self):
        ns = NewsSource(
            source_id="s2", name="Twitter", domain="twitter.com",
            reliability_score=0.3, source_type="SOCIAL", is_active=False,
        )
        assert ns.reliability_score == 0.3
        assert ns.is_active is False

    def test_news_event_defaults(self):
        ne = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges")
        assert ne.sentiment == "NEUTRAL"
        assert ne.sentiment_score == 0.0
        assert ne.confidence == 0.5
        assert ne.is_duplicate is False
        assert ne.source == "news_module"

    def test_news_event_custom(self):
        ne = NewsEvent(
            event_id="e2", asset="ETH", headline="Ethereum upgrade",
            sentiment="BULLISH", sentiment_score=0.8, confidence=0.9,
        )
        assert ne.sentiment == "BULLISH"
        assert ne.sentiment_score == 0.8

    def test_serialization(self):
        ne = NewsEvent(event_id="e1", asset="BTC", headline="Test")
        d = ne.to_dict()
        assert d["event_id"] == "e1"
        assert d["asset"] == "BTC"
        assert d["headline"] == "Test"
        assert "detected_at" in d


class TestNewsClassifier:

    def test_classify_bullish(self):
        nc = NewsClassifier()
        result = nc.classify_headline("Bitcoin surges to new all-time high")
        assert result == "BULLISH"

    def test_classify_bearish(self):
        nc = NewsClassifier()
        result = nc.classify_headline("Crypto crash leads to massive losses")
        assert result == "BEARISH"

    def test_classify_neutral(self):
        nc = NewsClassifier()
        result = nc.classify_headline("Bitcoin trading sideways today")
        assert result == "NEUTRAL"

    def test_sentiment_score_positive(self):
        nc = NewsClassifier()
        score = nc.calculate_sentiment_score("Bitcoin surges with massive gains")
        assert score > 0.0

    def test_sentiment_score_negative(self):
        nc = NewsClassifier()
        score = nc.calculate_sentiment_score("Bitcoin crash leads to heavy losses")
        assert score < 0.0

    def test_sentiment_score_neutral(self):
        nc = NewsClassifier()
        score = nc.calculate_sentiment_score("Bitcoin trading at 50000")
        assert score == 0.0

    def test_confidence_from_reliability(self):
        nc = NewsClassifier()
        conf = nc.calculate_confidence(0.8, "Bitcoin surges", body_length=600)
        assert conf > 0.5
        assert conf <= 1.0

    def test_confidence_low_reliability(self):
        nc = NewsClassifier()
        conf = nc.calculate_confidence(0.2, "Short", body_length=0)
        assert conf < 0.5

    def test_classify_event_sets_sentiment(self):
        nc = NewsClassifier()
        event = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges to record")
        result = nc.classify_event(event)
        assert result.sentiment == "BULLISH"
        assert result.sentiment_score > 0.0
        assert result.confidence > 0.0


class TestFreshnessValidator:

    def test_is_fresh_recent(self):
        validator = FreshnessValidator()
        event = NewsEvent(
            event_id="e1", asset="BTC", headline="Test",
            published_at=datetime.now(timezone.utc),
        )
        assert validator.is_fresh(event) is True

    def test_is_fresh_old(self):
        validator = FreshnessValidator(max_age_hours=1)
        event = NewsEvent(
            event_id="e1", asset="BTC", headline="Test",
            published_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        assert validator.is_fresh(event) is False

    def test_freshness_score_recent(self):
        validator = FreshnessValidator()
        event = NewsEvent(
            event_id="e1", asset="BTC", headline="Test",
            published_at=datetime.now(timezone.utc),
        )
        score = validator.freshness_score(event)
        assert score > 0.99

    def test_freshness_score_old(self):
        validator = FreshnessValidator(max_age_hours=24)
        event = NewsEvent(
            event_id="e1", asset="BTC", headline="Test",
            published_at=datetime.now(timezone.utc) - timedelta(hours=12),
        )
        score = validator.freshness_score(event)
        assert 0.0 < score < 1.0

    def test_freshness_score_expired(self):
        validator = FreshnessValidator(max_age_hours=1)
        event = NewsEvent(
            event_id="e1", asset="BTC", headline="Test",
            published_at=datetime.now(timezone.utc) - timedelta(hours=48),
        )
        assert validator.freshness_score(event) == 0.0


class TestDuplicateDetector:

    def test_is_duplicate_exact(self):
        dd = DuplicateDetector()
        event = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges")
        dd.mark_seen(event)
        dup = NewsEvent(event_id="e2", asset="BTC", headline="Bitcoin surges")
        assert dd.is_duplicate(dup) is True

    def test_is_duplicate_normalized(self):
        dd = DuplicateDetector()
        event = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges!!!")
        dd.mark_seen(event)
        dup = NewsEvent(event_id="e2", asset="BTC", headline="bitcoin surges")
        assert dd.is_duplicate(dup) is True

    def test_is_not_duplicate(self):
        dd = DuplicateDetector()
        event = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges")
        dd.mark_seen(event)
        other = NewsEvent(event_id="e2", asset="BTC", headline="Ethereum upgrade")
        assert dd.is_duplicate(other) is False

    def test_is_duplicate_existing_list(self):
        dd = DuplicateDetector()
        existing = [
            NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges"),
        ]
        dup = NewsEvent(event_id="e2", asset="BTC", headline="Bitcoin surges")
        assert dd.is_duplicate(dup, existing) is True

    def test_normalize_headline(self):
        dd = DuplicateDetector()
        result = dd.normalize_headline("Bitcoin SURGES!!! To $50k")
        assert "bitcoin" in result
        assert "surges" in result
        assert "!" not in result

    def test_clear(self):
        dd = DuplicateDetector()
        dd.mark_seen(NewsEvent(event_id="e1", asset="BTC", headline="Test"))
        assert len(dd.seen_headlines) == 1
        dd.clear()
        assert len(dd.seen_headlines) == 0


class TestNewsIntegration:

    def test_enabled_default(self):
        ni = NewsIntegration()
        assert ni.enabled is True

    def test_process_news_stores_event(self):
        ni = NewsIntegration()
        event = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges")
        result = ni.process_news(event)
        assert result is not None
        assert len(ni.events) == 1

    def test_process_news_disabled(self):
        ni = NewsIntegration()
        ni.enabled = False
        event = NewsEvent(event_id="e1", asset="BTC", headline="Test")
        result = ni.process_news(event)
        assert result is None

    def test_process_news_classifies(self):
        ni = NewsIntegration()
        event = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges to record high")
        result = ni.process_news(event)
        assert result.sentiment == "BULLISH"

    def test_process_news_duplicate(self):
        ni = NewsIntegration()
        e1 = NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges")
        ni.process_news(e1)
        e2 = NewsEvent(event_id="e2", asset="BTC", headline="Bitcoin surges")
        result = ni.process_news(e2)
        assert result.is_duplicate is True

    def test_register_source(self):
        ni = NewsIntegration()
        source = NewsSource(source_id="s1", name="CoinDesk", reliability_score=0.8)
        ni.register_source(source)
        assert "s1" in ni.sources

    def test_get_features_enabled(self):
        ni = NewsIntegration()
        features = ni.get_features()
        assert features["news_enabled"] is True
        assert "news_features" in features

    def test_get_features_disabled(self):
        ni = NewsIntegration()
        ni.enabled = False
        features = ni.get_features()
        assert features["news_enabled"] is False

    def test_get_features_tracks_counts(self):
        ni = NewsIntegration()
        ni.process_news(NewsEvent(event_id="e1", asset="BTC", headline="Bitcoin surges"))
        ni.process_news(NewsEvent(event_id="e2", asset="BTC", headline="Market crash fears"))
        features = ni.get_features()
        nf = features["news_features"]
        assert nf["total_events"] == 2
        assert nf["fresh_events"] == 2

    def test_get_contribution_log(self):
        ni = NewsIntegration()
        ni.process_news(NewsEvent(event_id="e1", asset="BTC", headline="Test"))
        log = ni.get_contribution_log()
        assert len(log) == 1
        assert log[0]["event_id"] == "e1"

    def test_evaluate_enabled(self):
        ni = NewsIntegration()
        result = ni.evaluate()
        assert result["ok"] is True
        assert result["news_available"] is True

    def test_evaluate_disabled(self):
        ni = NewsIntegration()
        ni.enabled = False
        result = ni.evaluate()
        assert result["ok"] is True
        assert result["news_available"] is False
