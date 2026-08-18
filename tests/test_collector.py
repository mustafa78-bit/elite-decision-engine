import time
from unittest.mock import MagicMock, patch

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
