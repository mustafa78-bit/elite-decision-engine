"""Architecture tests for intelligence data layer."""

from typing import Optional

import pytest

from market_data.base import IntelligenceProvider
from market_data.intelligence import (
    FeatureAvailability,
    IntelligenceBundle,
    IntelligenceCollector,
    MarketFeature,
    MissingDataHandler,
)


class TestMarketFeature:

    def test_basic_fields(self):
        f = MarketFeature(symbol="BTC", timestamp=1000, confidence=0.8)
        assert f.symbol == "BTC"
        assert f.timestamp == 1000
        assert f.confidence == 0.8

    def test_default_confidence(self):
        f = MarketFeature(symbol="BTC", timestamp=1000)
        assert f.confidence == 0.0

    def test_metadata_default(self):
        f = MarketFeature(symbol="BTC", timestamp=1000)
        assert f.metadata == {}

    def test_is_fresh_within_threshold(self):
        import time
        now = time.time()
        f = MarketFeature(symbol="BTC", timestamp=int(now))
        assert f.is_fresh(now=now, max_age=3600) is True

    def test_is_fresh_stale(self):
        f = MarketFeature(symbol="BTC", timestamp=1000)
        assert f.is_fresh(now=2000, max_age=100) is False

    def test_is_fresh_zero_timestamp(self):
        f = MarketFeature(symbol="BTC", timestamp=0)
        assert f.is_fresh() is False

    def test_is_fresh_millisecond_timestamp(self):
        import time
        now = time.time()
        ms_ts = int(now * 1000)
        f = MarketFeature(symbol="BTC", timestamp=ms_ts)
        assert f.is_fresh(now=now + 10, max_age=3600) is True


class TestMissingDataHandler:

    def test_safe_float_none(self):
        assert MissingDataHandler.safe_float(None) == 0.0

    def test_safe_float_valid(self):
        assert MissingDataHandler.safe_float(42.5) == 42.5

    def test_safe_float_string(self):
        assert MissingDataHandler.safe_float("abc") == 0.0

    def test_safe_int_none(self):
        assert MissingDataHandler.safe_int(None) == 0

    def test_safe_int_valid(self):
        assert MissingDataHandler.safe_int(42) == 42

    def test_safe_str_none(self):
        assert MissingDataHandler.safe_str(None) == "unknown"

    def test_safe_str_valid(self):
        assert MissingDataHandler.safe_str("hello") == "hello"

    def test_safe_dict_valid(self):
        d = {"key": "value"}
        assert MissingDataHandler.safe_dict(d) == d

    def test_safe_dict_none(self):
        assert MissingDataHandler.safe_dict(None) is None


class TestFeatureAvailability:

    def test_defaults(self):
        fa = FeatureAvailability()
        assert fa.funding is False
        assert fa.liquidity is False
        assert fa.order_flow is False
        assert fa.whale is False

    def test_active_features(self):
        fa = FeatureAvailability(funding=True, open_interest=True)
        active = fa.active_features
        assert "funding" in active
        assert "open_interest" in active
        assert "liquidity" not in active

    def test_active_features_empty(self):
        fa = FeatureAvailability()
        assert fa.active_features == []

    def test_active_features_partial(self):
        fa = FeatureAvailability(funding=True)
        assert fa.active_features == ["funding"]


class TestIntelligenceBundleFromBundle:

    def test_no_features(self):
        bundle = IntelligenceBundle.from_bundle(symbol="BTC")
        assert bundle.symbol == "BTC"
        assert bundle.feature_count == 0
        assert bundle.confidence == 0.0
        assert bundle.availability.all_available is False

    def test_single_feature_funding(self):
        bundle = IntelligenceBundle.from_bundle(
            symbol="BTC",
            funding_risk={"level": "neutral", "risk_score": 1.0},
        )
        assert bundle.feature_count == 1
        assert bundle.confidence == 1.0
        assert bundle.availability.funding is True
        assert bundle.availability.open_interest is False

    def test_single_feature_oi(self):
        bundle = IntelligenceBundle.from_bundle(
            symbol="BTC",
            oi_trend={"trend": "increase", "strength": 0.5},
        )
        assert bundle.feature_count == 1
        assert bundle.confidence == 0.5
        assert bundle.availability.open_interest is True
        assert bundle.availability.funding is False

    def test_both_features(self):
        bundle = IntelligenceBundle.from_bundle(
            symbol="BTC",
            funding_risk={"level": "neutral", "risk_score": 1.0},
            oi_trend={"trend": "increase", "strength": 0.5},
        )
        assert bundle.feature_count == 2
        assert bundle.confidence == 0.75
        assert bundle.availability.all_available is True

    def test_with_errors(self):
        bundle = IntelligenceBundle.from_bundle(
            symbol="BTC",
            errors=["API timeout"],
        )
        assert "API timeout" in bundle.errors

    def test_errors_default_empty(self):
        bundle = IntelligenceBundle.from_bundle(symbol="BTC")
        assert bundle.errors == ()


class TestIntelligenceProviderProtocol:

    def test_funding_collector_conforms(self):
        from market_data.funding.collector import FundingCollector
        assert isinstance(FundingCollector(), IntelligenceProvider)

    def test_oi_collector_conforms(self):
        from market_data.open_interest.collector import OpenInterestCollector
        assert isinstance(OpenInterestCollector(), IntelligenceProvider)

    def test_custom_collector_conforms(self):
        class CustomProvider:
            def fetch_all(self):
                return []

            def fetch_for_symbol(self, symbol: str) -> Optional[dict]:
                return None

            def check_freshness(self, symbol: str) -> dict:
                return {"fresh": True}

        provider = CustomProvider()
        assert isinstance(provider, IntelligenceProvider)
