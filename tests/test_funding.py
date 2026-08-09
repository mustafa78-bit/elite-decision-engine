"""Tests for funding rate data models and collection."""

from unittest.mock import MagicMock, patch

import pytest

from market_data.funding.collector import FundingCollector
from market_data.funding.models import (
    FundingRate,
    FundingResult,
    calculate_funding_trend,
    detect_extreme_funding,
    interpret_funding_risk,
    validate_funding_rate,
)


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

    def test_check_freshness_returns_dict(self):
        collector = FundingCollector()
        result = collector.check_freshness("BTC")
        assert isinstance(result, dict)
        assert "fresh" in result
