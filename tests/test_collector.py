import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from market_data.collector import HyperliquidCollector, _stale_threshold_seconds


class TestStaleThresholdSeconds:
    def test_scales_with_timeframe(self):
        # Regression: a flat 7200s (2h) threshold was actually calibrated for
        # 1h candles specifically (2x their own period) and never revisited
        # for other timeframes -- a 4h candle spent over half its real,
        # un-stale lifecycle looking "stale" under that fixed number.
        assert _stale_threshold_seconds("1h") == 7200
        assert _stale_threshold_seconds("4h") == 28800
        assert _stale_threshold_seconds("15m") == 1800
        assert _stale_threshold_seconds("1d") == 172800

    def test_unknown_timeframe_falls_back_to_1h_equivalent(self):
        assert _stale_threshold_seconds("3d") == 7200


def _candle(ts_ms: float) -> dict:
    return {"t": ts_ms, "o": "100", "h": "101", "l": "99", "c": "100.5", "v": "10"}


class TestHyperliquidCollectorStaleness:
    def test_4h_candle_three_hours_old_is_not_stale(self):
        # Would have been incorrectly dropped under the old flat 7200s (2h)
        # threshold, despite being completely normal for a 4h candle.
        three_hours_ago_ms = (time.time() - 3 * 3600) * 1000
        collector = HyperliquidCollector()
        mock_response = MagicMock()
        mock_response.json.return_value = [_candle(three_hours_ago_ms)]
        mock_response.raise_for_status.return_value = None
        with patch.object(collector._session, "post", return_value=mock_response):
            df = collector.get_ohlcv(symbol="BTC", timeframe="4h")
        assert not df.empty

    def test_4h_candle_nine_hours_old_is_stale(self):
        nine_hours_ago_ms = (time.time() - 9 * 3600) * 1000
        collector = HyperliquidCollector()
        mock_response = MagicMock()
        mock_response.json.return_value = [_candle(nine_hours_ago_ms)]
        mock_response.raise_for_status.return_value = None
        with patch.object(collector._session, "post", return_value=mock_response):
            df = collector.get_ohlcv(symbol="BTC", timeframe="4h")
        assert df.empty

    def test_1h_candle_three_hours_old_is_still_stale(self):
        # The 1h behavior itself must not regress -- same 7200s threshold as before.
        three_hours_ago_ms = (time.time() - 3 * 3600) * 1000
        collector = HyperliquidCollector()
        mock_response = MagicMock()
        mock_response.json.return_value = [_candle(three_hours_ago_ms)]
        mock_response.raise_for_status.return_value = None
        with patch.object(collector._session, "post", return_value=mock_response):
            df = collector.get_ohlcv(symbol="BTC", timeframe="1h")
        assert df.empty


def _http_error(status_code: int) -> requests.HTTPError:
    resp = MagicMock()
    resp.status_code = status_code
    return requests.HTTPError(response=resp)


class TestHyperliquidCollectorRetryBehavior:
    """A 429 must not be blindly retried -- confirmed live 2026-08-21: doing
    so compounds the very rate-limit pressure that triggered it (236 429s
    in a short window with the old behavior, many subsystems retrying
    independently into repeated bursts)."""

    def test_429_fails_fast_without_retrying(self):
        collector = HyperliquidCollector()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = _http_error(429)

        with patch.object(collector._session, "post", return_value=mock_response) as mock_post, \
             patch("market_data.collector.time.sleep") as mock_sleep:
            with pytest.raises(requests.HTTPError):
                collector.get_ohlcv(symbol="BTC", timeframe="1h")

        mock_post.assert_called_once()
        mock_sleep.assert_not_called()

    def test_non_429_http_error_still_retries(self):
        # The blind-retry behavior is still correct/desired for transient
        # errors that aren't a rate-limit signal (e.g. a real 500).
        collector = HyperliquidCollector()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = _http_error(500)

        with patch.object(collector._session, "post", return_value=mock_response) as mock_post, \
             patch("market_data.collector.time.sleep") as mock_sleep:
            with pytest.raises(requests.HTTPError):
                collector.get_ohlcv(symbol="BTC", timeframe="1h")

        assert mock_post.call_count == HyperliquidCollector.MAX_RETRIES
        assert mock_sleep.call_count == HyperliquidCollector.MAX_RETRIES - 1

    def test_connection_error_still_retries(self):
        collector = HyperliquidCollector()

        with patch.object(
            collector._session, "post", side_effect=requests.ConnectionError("network down")
        ) as mock_post, patch("market_data.collector.time.sleep") as mock_sleep:
            with pytest.raises(requests.ConnectionError):
                collector.get_ohlcv(symbol="BTC", timeframe="1h")

        assert mock_post.call_count == HyperliquidCollector.MAX_RETRIES
        assert mock_sleep.call_count == HyperliquidCollector.MAX_RETRIES - 1
