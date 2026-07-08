"""Tests for open interest data models and collection."""

import pytest

from market_data.open_interest.models import (
    OpenInterest,
    OpenInterestResult,
    detect_oi_trend,
)
from market_data.open_interest.collector import OpenInterestCollector


class TestOpenInterest:

    def test_basic_fields(self):
        oi = OpenInterest(symbol="BTC", value=1_000_000_000, timestamp=1000)
        assert oi.symbol == "BTC"
        assert oi.value == 1_000_000_000
        assert oi.timestamp == 1000

    def test_with_changes(self):
        oi = OpenInterest(symbol="ETH", value=500_000_000, timestamp=1000, change_1h=0.05, change_24h=0.10)
        assert oi.change_1h == 0.05
        assert oi.change_24h == 0.10


class TestOpenInterestResult:

    def test_empty(self):
        result = OpenInterestResult()
        assert result.empty is True
        assert result.latest is None

    def test_with_records(self):
        oi = OpenInterest(symbol="BTC", value=1_000_000_000, timestamp=1000)
        result = OpenInterestResult(records=(oi,))
        assert result.empty is False
        assert result.latest == oi

    def test_for_symbol(self):
        oi1 = OpenInterest(symbol="BTC", value=1_000_000_000, timestamp=1000)
        oi2 = OpenInterest(symbol="ETH", value=500_000_000, timestamp=1000)
        result = OpenInterestResult(records=(oi1, oi2))
        assert result.for_symbol("BTC") == oi1
        assert result.for_symbol("SOL") is None


class TestDetectOITrend:

    def test_insufficient_data(self):
        result = detect_oi_trend([OpenInterest(symbol="BTC", value=1_000_000_000, timestamp=1000)])
        assert result["trend"] == "unknown"

    def test_increasing_trend(self):
        records = [
            OpenInterest(symbol="BTC", value=1_000_000, timestamp=1000),
            OpenInterest(symbol="BTC", value=1_030_000, timestamp=2000),
        ]
        result = detect_oi_trend(records)
        assert result["trend"] == "increase"

    def test_decreasing_trend(self):
        records = [
            OpenInterest(symbol="BTC", value=1_000_000, timestamp=1000),
            OpenInterest(symbol="BTC", value=970_000, timestamp=2000),
        ]
        result = detect_oi_trend(records)
        assert result["trend"] == "decrease"

    def test_strong_increase(self):
        records = [
            OpenInterest(symbol="BTC", value=1_000_000, timestamp=1000),
            OpenInterest(symbol="BTC", value=1_200_000, timestamp=2000),
        ]
        result = detect_oi_trend(records)
        assert "strong" in result["trend"]

    def test_neutral(self):
        records = [
            OpenInterest(symbol="BTC", value=1_000_000, timestamp=1000),
            OpenInterest(symbol="BTC", value=1_005_000, timestamp=2000),
        ]
        result = detect_oi_trend(records)
        assert result["trend"] == "neutral"

    def test_returns_expected_keys(self):
        records = [
            OpenInterest(symbol="BTC", value=1_000_000, timestamp=1000),
            OpenInterest(symbol="BTC", value=1_100_000, timestamp=2000),
        ]
        result = detect_oi_trend(records)
        assert "trend" in result
        assert "strength" in result
        assert "avg_change_pct" in result
        assert "current_value" in result


class TestOpenInterestCollector:

    def test_fetch_all_returns_result(self):
        collector = OpenInterestCollector()
        result = collector.fetch_all()
        assert isinstance(result, OpenInterestResult)

    def test_fetch_for_symbol_returns_oi_or_none(self):
        collector = OpenInterestCollector()
        oi = collector.fetch_for_symbol("BTC")
        if oi is not None:
            assert isinstance(oi, OpenInterest)
            assert oi.value > 0

    def test_fetch_with_trend_returns_dict(self):
        collector = OpenInterestCollector()
        result = collector.fetch_with_trend("BTC")
        assert isinstance(result, dict)
        assert "symbol" in result
        assert "trend" in result
