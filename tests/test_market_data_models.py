"""Tests for market data models and validation."""

import pandas as pd
import pytest

from market_data.models import (
    OHLCV,
    OHLCVResult,
    check_timestamp_freshness,
    validate_ohlcv_result,
)


class TestOHLCV:

    def test_basic_fields(self):
        c = OHLCV(timestamp=1000, open=100.0, high=110.0, low=90.0, close=105.0, volume=1000.0)
        assert c.open == 100.0
        assert c.high == 110.0
        assert c.close == 105.0

    def test_frozen(self):
        c = OHLCV(timestamp=1, open=1, high=2, low=1, close=1.5, volume=100)
        with pytest.raises(Exception):
            c.close = 200.0


class TestOHLCVResult:

    def test_empty_result(self):
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=())
        assert r.empty is True
        assert r.latest is None
        assert r.is_stale is True

    def test_with_candles(self):
        c = OHLCV(timestamp=1000, open=100, high=110, low=90, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        assert r.empty is False
        assert r.latest == c
        assert r.symbol == "BTC"

    def test_latest_returns_last_candle(self):
        c1 = OHLCV(timestamp=1, open=10, high=11, low=9, close=10.5, volume=100)
        c2 = OHLCV(timestamp=2, open=10.5, high=12, low=10, close=11, volume=200)
        r = OHLCVResult(symbol="ETH", timeframe="4h", candles=(c1, c2))
        assert r.latest == c2

    def test_to_dataframe(self):
        c = OHLCV(timestamp=1000, open=100, high=110, low=90, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        df = r.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["close"] == 105.0

    def test_to_dataframe_empty(self):
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=())
        df = r.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_from_dataframe(self):
        df = pd.DataFrame({
            "timestamp": [1000, 2000],
            "open": [100.0, 200.0],
            "high": [110.0, 210.0],
            "low": [90.0, 190.0],
            "close": [105.0, 205.0],
            "volume": [1000.0, 2000.0],
        })
        result = OHLCVResult.from_dataframe(df, "BTC", "1h")
        assert result.symbol == "BTC"
        assert result.timeframe == "1h"
        assert len(result.candles) == 2
        assert result.candles[0].close == 105.0
        assert result.candles[1].close == 205.0

    def test_from_dataframe_empty(self):
        result = OHLCVResult.from_dataframe(pd.DataFrame(), "BTC", "1h")
        assert result.empty is True

    def test_from_dataframe_none(self):
        result = OHLCVResult.from_dataframe(None, "BTC", "1h")
        assert result.empty is True


class TestValidateOHLCVResult:

    def test_valid_candles_no_errors(self):
        c = OHLCV(timestamp=1000, open=100, high=110, low=90, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        errors = validate_ohlcv_result(r)
        assert errors == []

    def test_empty_result_errors(self):
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=())
        errors = validate_ohlcv_result(r)
        assert "No candles" in errors

    def test_high_below_low(self):
        c = OHLCV(timestamp=1, open=100, high=80, low=120, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        errors = validate_ohlcv_result(r)
        assert any("high" in e and "low" in e for e in errors)

    def test_negative_volume(self):
        c = OHLCV(timestamp=1, open=100, high=110, low=90, close=105, volume=-100)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        errors = validate_ohlcv_result(r)
        assert any("negative volume" in e for e in errors)

    def test_non_positive_open(self):
        c = OHLCV(timestamp=1, open=0, high=110, low=90, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        errors = validate_ohlcv_result(r)
        assert any("non-positive open" in e for e in errors)


class TestCheckTimestampFreshness:

    def test_fresh_data(self):
        import time
        now = time.time()
        c = OHLCV(timestamp=int(now), open=100, high=110, low=90, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        fresh, msg = check_timestamp_freshness(r, now=now, max_age_seconds=3600)
        assert fresh is True
        assert msg is None

    def test_stale_data(self):
        old_ts = 1000000
        c = OHLCV(timestamp=old_ts, open=100, high=110, low=90, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        fresh, msg = check_timestamp_freshness(r, now=old_ts + 10000, max_age_seconds=3600)
        assert fresh is False
        assert msg is not None

    def test_millisecond_timestamp(self):
        import time
        now = time.time()
        ms_ts = int(now * 1000)
        c = OHLCV(timestamp=ms_ts, open=100, high=110, low=90, close=105, volume=1000)
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=(c,))
        fresh, msg = check_timestamp_freshness(r, now=now + 100, max_age_seconds=3600)
        assert fresh is True

    def test_empty_result_not_fresh(self):
        r = OHLCVResult(symbol="BTC", timeframe="1h", candles=())
        fresh, msg = check_timestamp_freshness(r)
        assert fresh is False
        assert msg is not None
