"""Tests for open interest data models and collection."""

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from market_data.open_interest.collector import OpenInterestCollector
from market_data.open_interest.models import (
    OpenInterest,
    OpenInterestResult,
    detect_oi_trend,
)


@pytest.fixture(autouse=True)
def _reset_open_interest_collector_cache():
    # See test_funding.py's identical fixture -- OpenInterestCollector's
    # fetch_all() now caches at the class level for the same reason.
    OpenInterestCollector._cache = None
    yield
    OpenInterestCollector._cache = None


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

    def test_fetch_with_trend_accumulates_real_history_across_calls(self):
        # Regression: fetch_with_trend() previously wrapped only the current
        # snapshot in a single-element list before calling detect_oi_trend(),
        # which requires len(records) >= 2 -- so it always returned
        # trend="unknown", strength=0.0 regardless of real OI movement. It
        # now accumulates a real rolling history across calls, so a genuine
        # trend becomes available once called at least twice for a symbol.
        collector = OpenInterestCollector()
        snapshots = [
            OpenInterest(symbol="BTC", value=1000.0, timestamp=1),
            OpenInterest(symbol="BTC", value=1200.0, timestamp=2),
        ]
        with patch.object(collector, "fetch_for_symbol", side_effect=snapshots):
            first = collector.fetch_with_trend("BTC")
            assert first["trend"] == "unknown"

            second = collector.fetch_with_trend("BTC")
            assert second["trend"] != "unknown"


class TestOpenInterestCollectorCaching:

    @staticmethod
    def _mock_response():
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {"universe": [{"name": "BTC"}]},
            [{"openInterest": "1000000.0"}],
        ]
        return mock_response

    def test_repeated_calls_on_same_instance_hit_network_once(self):
        collector = OpenInterestCollector()
        with patch.object(collector._session, "post", return_value=self._mock_response()) as mock_post:
            first = collector.fetch_all()
            second = collector.fetch_all()

        assert mock_post.call_count == 1
        assert first == second

    def test_repeated_calls_across_separate_instances_hit_network_once(self):
        first_collector = OpenInterestCollector()
        second_collector = OpenInterestCollector()
        response = self._mock_response()

        with patch.object(first_collector._session, "post", return_value=response) as mock_post_one:
            first = first_collector.fetch_all()
        with patch.object(second_collector._session, "post", return_value=response) as mock_post_two:
            second = second_collector.fetch_all()

        assert mock_post_one.call_count == 1
        assert mock_post_two.call_count == 0
        assert first == second

    def test_cache_expires_after_ttl(self):
        collector = OpenInterestCollector()
        with patch.object(collector._session, "post", return_value=self._mock_response()) as mock_post:
            collector.fetch_all()
            with patch(
                "market_data.open_interest.collector.time.time",
                return_value=time.time() + OpenInterestCollector._CACHE_TTL_SECONDS + 1,
            ):
                collector.fetch_all()

        assert mock_post.call_count == 2

    def test_failed_fetch_does_not_poison_cache(self):
        collector = OpenInterestCollector()
        with patch.object(collector._session, "post", side_effect=requests.RequestException("boom")):
            result = collector.fetch_all()
        assert result.records == ()
        assert OpenInterestCollector._cache is None

        with patch.object(collector._session, "post", return_value=self._mock_response()) as mock_post:
            result = collector.fetch_all()
        assert mock_post.call_count == 1
        assert len(result.records) == 1
