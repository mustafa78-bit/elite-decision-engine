"""Tests for market intelligence integration."""

from unittest.mock import patch

import pytest

from market_data.funding.models import FundingRate, FundingResult
from market_data.intelligence import (
    FeatureAvailability,
    IntelligenceBundle,
    IntelligenceCollector,
)
from market_data.open_interest.models import OpenInterest, OpenInterestResult


class TestFeatureAvailability:

    def test_all_unavailable(self):
        fa = FeatureAvailability()
        assert fa.funding is False
        assert fa.open_interest is False
        assert fa.all_available is False

    def test_all_available(self):
        fa = FeatureAvailability(funding=True, open_interest=True)
        assert fa.all_available is True

    def test_partial_availability(self):
        fa = FeatureAvailability(funding=True, open_interest=False)
        assert fa.funding is True
        assert fa.open_interest is False
        assert fa.all_available is False


class TestIntelligenceBundle:

    def test_basic_fields(self):
        bundle = IntelligenceBundle(symbol="BTC")
        assert bundle.symbol == "BTC"
        assert bundle.funding_risk is None
        assert bundle.oi_trend is None
        assert bundle.availability.all_available is False
        assert bundle.errors == ()

    def test_with_funding_risk(self):
        bundle = IntelligenceBundle(
            symbol="BTC",
            funding_risk={"level": "neutral", "risk_score": 1.0},
            availability=FeatureAvailability(funding=True),
        )
        assert bundle.funding_risk["level"] == "neutral"

    def test_with_errors(self):
        bundle = IntelligenceBundle(symbol="BTC", errors=("API error",))
        assert "API error" in bundle.errors


class TestIntelligenceCollector:

    def test_collect_with_mock_funding_and_oi(self):
        mock_funding = FundingCollectorMock()
        mock_oi = OICollectorMock()
        collector = IntelligenceCollector(
            funding_collector=mock_funding,
            oi_collector=mock_oi,
        )
        bundle = collector.collect("BTC")
        assert bundle.symbol == "BTC"
        assert bundle.funding_risk is not None
        assert bundle.oi_trend is not None
        assert bundle.availability.all_available is True
        assert bundle.errors == ()

    def test_collect_with_funding_only(self):
        mock_funding = FundingCollectorMock()
        mock_oi = EmptyOICollectorMock()
        collector = IntelligenceCollector(
            funding_collector=mock_funding,
            oi_collector=mock_oi,
        )
        bundle = collector.collect("BTC")
        assert bundle.funding_risk is not None
        assert bundle.oi_trend is None
        assert bundle.availability.funding is True
        assert bundle.availability.open_interest is False
        assert any("OI" in e for e in bundle.errors)

    def test_collect_with_funding_error(self):
        mock_funding = FailingFundingCollectorMock()
        mock_oi = OICollectorMock()
        collector = IntelligenceCollector(
            funding_collector=mock_funding,
            oi_collector=mock_oi,
        )
        bundle = collector.collect("BTC")
        assert bundle.funding_risk is None
        assert bundle.oi_trend is not None
        assert bundle.availability.funding is False
        assert bundle.availability.open_interest is True
        assert any("error" in e.lower() for e in bundle.errors)

    def test_collect_with_all_errors(self):
        mock_funding = FailingFundingCollectorMock()
        mock_oi = FailingOICollectorMock()
        collector = IntelligenceCollector(
            funding_collector=mock_funding,
            oi_collector=mock_oi,
        )
        bundle = collector.collect("BTC")
        assert bundle.funding_risk is None
        assert bundle.oi_trend is None
        assert bundle.availability.all_available is False
        assert len(bundle.errors) == 2

    def test_default_constructors(self):
        with patch("market_data.intelligence.FundingCollector") as fc_mock, \
             patch("market_data.intelligence.OpenInterestCollector") as oi_mock:
            collector = IntelligenceCollector()
            fc_mock.assert_called_once()
            oi_mock.assert_called_once()
            assert collector.funding is not None
            assert collector.oi is not None


class FundingCollectorMock:
    def fetch_for_symbol(self, symbol):
        return FundingRate(symbol=symbol, rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)

    def collect(self, symbol):
        return FundingResult(rates=(FundingRate(symbol=symbol, rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800),))


class EmptyOICollectorMock:
    def fetch_with_trend(self, symbol):
        return {"symbol": symbol, "value": 0, "trend": "unknown", "strength": 0.0}


class OICollectorMock:
    def fetch_with_trend(self, symbol):
        return {"symbol": symbol, "value": 1_000_000_000, "trend": "neutral", "strength": 0.0}


class FailingFundingCollectorMock:
    def fetch_for_symbol(self, symbol):
        raise Exception("Funding API unavailable")


class FailingOICollectorMock:
    def fetch_with_trend(self, symbol):
        raise Exception("OI API unavailable")
