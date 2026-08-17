"""Tests for funding rate data models and collection."""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from market_data.funding.collector import FundingCollector
from market_data.funding.models import (
    FundingRate,
    FundingResult,
    calculate_funding_trend,
    detect_extreme_funding,
    interpret_funding_risk,
    validate_funding_rate,
)


@pytest.fixture(autouse=True)
def _reset_funding_collector_cache():
    # FundingCollector.fetch_all() now caches at the class level (see that
    # class's _CACHE_TTL_SECONDS comment) -- without resetting between
    # tests, a real network call in one test (e.g.
    # test_fetch_all_returns_result) would silently serve its cached result
    # to a later test that mocks collector._session.post and expects that
    # mock to actually be hit.
    FundingCollector._cache = None
    yield
    FundingCollector._cache = None


class TestFundingRate:

    def test_basic_fields(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        assert rate.symbol == "BTC"
        assert rate.rate == 0.0001
        assert rate.is_positive is True
        assert rate.is_negative is False

    def test_negative_rate(self):
        rate = FundingRate(symbol="ETH", rate=-0.0005, timestamp=1000, next_funding_time=1000 + 28800)
        assert rate.is_positive is False
        assert rate.is_negative is True

    def test_annualized_rate(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800, interval_hours=8)
        # 0.0001 * (365.25 * 24 / 8) = 0.0001 * 1095.75 = 0.109575
        assert rate.annualized_rate == pytest.approx(0.109575, rel=0.01)

    def test_zero_rate(self):
        rate = FundingRate(symbol="BTC", rate=0.0, timestamp=1000, next_funding_time=1000 + 28800)
        assert rate.is_positive is False
        assert rate.is_negative is False
        assert rate.annualized_rate == 0.0


class TestFundingResult:

    def test_empty(self):
        result = FundingResult()
        assert result.empty is True
        assert result.latest is None

    def test_with_rates(self):
        r1 = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        r2 = FundingRate(symbol="ETH", rate=-0.0002, timestamp=1000, next_funding_time=1000 + 28800)
        result = FundingResult(rates=(r1, r2))
        assert result.empty is False
        assert result.latest == r2

    def test_rate_for(self):
        r1 = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        result = FundingResult(rates=(r1,))
        assert result.rate_for("BTC") == r1
        assert result.rate_for("ETH") is None

    def test_is_fresh(self):
        import time
        now = time.time()
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=int(now), next_funding_time=int(now) + 28800)
        result = FundingResult(rates=(rate,))
        assert result.is_fresh is True

    def test_is_stale(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        result = FundingResult(rates=(rate,))
        assert result.is_fresh is False


class TestValidateFundingRate:

    def test_valid(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        assert validate_funding_rate(rate) == []

    def test_invalid_timestamp(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=0, next_funding_time=0)
        errors = validate_funding_rate(rate)
        assert len(errors) > 0

    def test_invalid_interval(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800, interval_hours=0)
        errors = validate_funding_rate(rate)
        assert any("interval" in e for e in errors)


class TestFundingRateToScoreInput:

    def test_neutral_rate(self):
        rate = FundingRate(symbol="BTC", rate=0.00001, timestamp=1000, next_funding_time=1000 + 28800)
        result = rate.to_score_input()
        assert result["funding_score"] == 1.0
        assert result["funding_is_positive"] is True

    def test_extreme_rate(self):
        rate = FundingRate(symbol="BTC", rate=0.05, timestamp=1000, next_funding_time=1000 + 28800)
        result = rate.to_score_input()
        assert result["funding_score"] == 0.0

    def test_elevated_rate(self):
        rate = FundingRate(symbol="BTC", rate=0.005, timestamp=1000, next_funding_time=1000 + 28800)
        result = rate.to_score_input()
        assert result["funding_score"] == 0.6

    def test_returns_expected_keys(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        result = rate.to_score_input()
        assert "funding_rate" in result
        assert "funding_annualized" in result
        assert "funding_score" in result
        assert "funding_is_positive" in result


class TestCalculateFundingTrend:

    def test_insufficient_data(self):
        trend = calculate_funding_trend([])
        assert trend["trend"] == "unknown"
        assert trend["strength"] == 0.0

    def test_single_rate(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        trend = calculate_funding_trend([rate])
        assert trend["trend"] == "unknown"

    def test_increasing_trend(self):
        r1 = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        r2 = FundingRate(symbol="BTC", rate=0.0003, timestamp=2000, next_funding_time=1000 + 28800)
        trend = calculate_funding_trend([r1, r2])
        assert "increase" in trend["trend"]
        assert trend["strength"] >= 0.3

    def test_decreasing_trend(self):
        r1 = FundingRate(symbol="BTC", rate=0.0003, timestamp=1000, next_funding_time=1000 + 28800)
        r2 = FundingRate(symbol="BTC", rate=0.0001, timestamp=2000, next_funding_time=1000 + 28800)
        trend = calculate_funding_trend([r1, r2])
        assert "decrease" in trend["trend"]

    def test_stable_trend(self):
        r1 = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        r2 = FundingRate(symbol="BTC", rate=0.000101, timestamp=2000, next_funding_time=1000 + 28800)
        trend = calculate_funding_trend([r1, r2])
        assert trend["trend"] == "stable"

    def test_returns_expected_keys(self):
        r1 = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        r2 = FundingRate(symbol="BTC", rate=0.0002, timestamp=2000, next_funding_time=1000 + 28800)
        trend = calculate_funding_trend([r1, r2])
        assert "trend" in trend
        assert "strength" in trend
        assert "avg_change_pct" in trend
        assert "current_annualized" in trend
        assert "average_annualized" in trend


class TestDetectExtremeFunding:

    def test_extreme_positive(self):
        rate = FundingRate(symbol="BTC", rate=0.05, timestamp=1000, next_funding_time=1000 + 28800)
        result = detect_extreme_funding(rate)
        assert result["is_extreme"] is True
        assert result["category"] == "extreme_positive"
        assert result["warning"] is not None

    def test_extreme_negative(self):
        rate = FundingRate(symbol="BTC", rate=-0.05, timestamp=1000, next_funding_time=1000 + 28800)
        result = detect_extreme_funding(rate)
        assert result["is_extreme"] is True
        assert result["category"] == "extreme_negative"

    def test_neutral(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        result = detect_extreme_funding(rate)
        assert result["is_extreme"] is False
        assert result["category"] == "neutral"

    def test_elevated(self):
        rate = FundingRate(symbol="BTC", rate=0.005, timestamp=1000, next_funding_time=1000 + 28800)
        result = detect_extreme_funding(rate)
        assert result["is_extreme"] is False
        assert result["category"] == "elevated_positive"

    def test_suggestion_on_extreme(self):
        rate = FundingRate(symbol="BTC", rate=0.05, timestamp=1000, next_funding_time=1000 + 28800)
        result = detect_extreme_funding(rate)
        assert result["suggestion"] is not None

    def test_no_suggestion_normal(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        result = detect_extreme_funding(rate)
        assert result["suggestion"] is None


class TestInterpretFundingRisk:

    def test_neutral(self):
        rate = FundingRate(symbol="BTC", rate=0.00001, timestamp=1000, next_funding_time=1000 + 28800)
        result = interpret_funding_risk(rate)
        assert result["level"] == "neutral"
        assert result["risk_score"] == 1.0

    def test_extreme_positive(self):
        rate = FundingRate(symbol="BTC", rate=0.05, timestamp=1000, next_funding_time=1000 + 28800)
        result = interpret_funding_risk(rate)
        assert result["level"] == "extreme"
        assert result["risk_score"] == 0.0

    def test_high_negative(self):
        rate = FundingRate(symbol="BTC", rate=-0.02, timestamp=1000, next_funding_time=1000 + 28800)
        result = interpret_funding_risk(rate)
        assert "negative" in result["level"]
        assert result["risk_score"] == 0.3

    def test_elevated(self):
        rate = FundingRate(symbol="BTC", rate=0.005, timestamp=1000, next_funding_time=1000 + 28800)
        result = interpret_funding_risk(rate)
        assert result["level"] == "elevated"
        assert result["risk_score"] == 0.6

    def test_returns_expected_keys(self):
        rate = FundingRate(symbol="BTC", rate=0.0001, timestamp=1000, next_funding_time=1000 + 28800)
        result = interpret_funding_risk(rate)
        assert "symbol" in result
        assert "annualized_rate" in result
        assert "level" in result
        assert "risk_score" in result
        assert "is_positive" in result


class TestFundingCollector:

    def test_fetch_all_returns_result(self):
        collector = FundingCollector()
        result = collector.fetch_all()
        assert isinstance(result, FundingResult)

    def test_fetch_all_returns_real_funding_rates_not_mid_prices(self):
        # Regression: fetch_all() previously hit allMids (current mid-market
        # PRICES, e.g. ~60000.0 for BTC) and stored the raw price directly as
        # FundingRate.rate. metaAndAssetCtxs returns [meta, assetCtxs] where
        # meta["universe"][i] and assetCtxs[i] describe the same asset.
        collector = FundingCollector()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {"universe": [{"name": "BTC"}, {"name": "ETH"}]},
            [{"funding": "0.0000125", "markPx": "60000.0"}, {"funding": "-0.00008", "markPx": "3000.0"}],
        ]
        with patch.object(collector._session, "post", return_value=mock_response):
            result = collector.fetch_all()

        assert len(result.rates) == 2
        btc = result.rate_for("BTC")
        assert btc is not None
        assert btc.rate == pytest.approx(0.0000125)
        # A real funding rate stays in a sane annualized range -- the old bug
        # (raw price as rate) produced an astronomical annualized_rate.
        assert abs(btc.annualized_rate) < 10.0

        eth = result.rate_for("ETH")
        assert eth is not None
        assert eth.rate == pytest.approx(-0.00008)

    def test_fetch_all_returns_empty_on_unexpected_shape(self):
        collector = FundingCollector()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"mids": {"BTC": "60000.0"}}
        with patch.object(collector._session, "post", return_value=mock_response):
            result = collector.fetch_all()
        assert result.rates == ()

    def test_concurrent_cache_miss_only_fires_one_network_call(self):
        # Regression: N concurrent callers all seeing a stale/empty cache at
        # once (e.g. every scanner symbol firing at process startup) each
        # used to fire their own network call before any of them populated
        # the cache -- the exact thundering-herd burst that trips
        # Hyperliquid's real rate limit. Only the first should hit the
        # network; the rest should block on the lock and reuse its result.
        collector = FundingCollector()
        call_count = 0
        call_lock = threading.Lock()

        def slow_post(*args, **kwargs):
            nonlocal call_count
            with call_lock:
                call_count += 1
            time.sleep(0.05)  # widen the race window
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = [
                {"universe": [{"name": "BTC"}]},
                [{"funding": "0.0000125"}],
            ]
            return mock_response

        with patch.object(collector._session, "post", side_effect=slow_post):
            threads = [threading.Thread(target=collector.fetch_all) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        assert call_count == 1

    def test_fetch_for_symbol_returns_rate_or_none(self):
        collector = FundingCollector()
        rate = collector.fetch_for_symbol("BTC")
        if rate is not None:
            assert isinstance(rate, FundingRate)
            assert rate.symbol == "BTC"

    def test_fetch_funding_history_returns_result(self):
        collector = FundingCollector()
        result = collector.fetch_funding_history("BTC", limit=1)
        assert isinstance(result, FundingResult)

    def test_fetch_funding_history_uses_real_request_shape_and_derives_interval(self):
        # Regression: the payload used to be {"req": {"coin": ..., "limit":
        # ...}}, which Hyperliquid's real API always 422's on -- the real
        # shape is top-level "coin"/"startTime". Real entries also never
        # include an "interval" field, so interval_hours must be derived
        # from consecutive entry timestamps (here: hourly, not the old
        # hardcoded 8h default) rather than guessed.
        collector = FundingCollector()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {"coin": "BTC", "fundingRate": "0.0000030", "time": 1_000_000_000},
            {"coin": "BTC", "fundingRate": "0.0000086", "time": 1_000_000_000 + 3_600_000},
            {"coin": "BTC", "fundingRate": "0.0000051", "time": 1_000_000_000 + 7_200_000},
        ]
        with patch.object(collector._session, "post", return_value=mock_response) as mock_post:
            result = collector.fetch_funding_history("BTC", limit=3)

        call_payload = mock_post.call_args.kwargs["json"]
        assert call_payload["type"] == "fundingHistory"
        assert call_payload["coin"] == "BTC"
        assert "startTime" in call_payload
        assert "req" not in call_payload

        assert len(result.rates) == 3
        for rate in result.rates:
            assert rate.interval_hours == pytest.approx(1.0, abs=0.01)

    def test_check_freshness_returns_dict(self):
        collector = FundingCollector()
        result = collector.check_freshness("BTC")
        assert isinstance(result, dict)
        assert "fresh" in result


class TestFundingCollectorCaching:

    @staticmethod
    def _mock_response():
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {"universe": [{"name": "BTC"}]},
            [{"funding": "0.0001", "markPx": "60000.0"}],
        ]
        return mock_response

    def test_repeated_calls_on_same_instance_hit_network_once(self):
        collector = FundingCollector()
        with patch.object(collector._session, "post", return_value=self._mock_response()) as mock_post:
            first = collector.fetch_all()
            second = collector.fetch_all()

        assert mock_post.call_count == 1
        assert first == second

    def test_repeated_calls_across_separate_instances_hit_network_once(self):
        # The cache is class-level, not per-instance -- this is what lets
        # the many independent call sites (api/routes/funding.py,
        # HyperliquidProvider, WhaleService, ...) share one real fetch
        # instead of each firing their own.
        first_collector = FundingCollector()
        second_collector = FundingCollector()
        response = self._mock_response()

        with patch.object(first_collector._session, "post", return_value=response) as mock_post_one:
            first = first_collector.fetch_all()
        with patch.object(second_collector._session, "post", return_value=response) as mock_post_two:
            second = second_collector.fetch_all()

        assert mock_post_one.call_count == 1
        assert mock_post_two.call_count == 0
        assert first == second

    def test_cache_expires_after_ttl(self):
        collector = FundingCollector()
        with patch.object(collector._session, "post", return_value=self._mock_response()) as mock_post:
            collector.fetch_all()
            with patch(
                "market_data.funding.collector.time.time",
                return_value=time.time() + FundingCollector._CACHE_TTL_SECONDS + 1,
            ):
                collector.fetch_all()

        assert mock_post.call_count == 2

    def test_failed_fetch_does_not_poison_cache(self):
        collector = FundingCollector()
        with patch.object(collector._session, "post", side_effect=requests.RequestException("boom")):
            result = collector.fetch_all()
        assert result.rates == ()
        assert FundingCollector._cache is None

        with patch.object(collector._session, "post", return_value=self._mock_response()) as mock_post:
            result = collector.fetch_all()
        assert mock_post.call_count == 1
        assert len(result.rates) == 1
