"""Tests for live market data engine."""

import pandas as pd

from market_data.live.engine import LiveMarketEngine, MarketSnapshot


class _MockCollector:
    def __init__(self, df):
        self.df = df

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return self.df


def _make_df(n, close_start=100.0, close_step=1.0):
    closes = [close_start + i * close_step for i in range(n)]
    return pd.DataFrame({
        "timestamp": list(range(n)),
        "open": closes, "high": [c + 1 for c in closes], "low": [c - 1 for c in closes],
        "close": closes, "volume": [10.0] * n,
    })


class TestMarketSnapshot:
    def test_snapshot_returns_snapshot(self):
        engine = LiveMarketEngine()
        snap = engine.snapshot(symbol="BTC")
        assert isinstance(snap, MarketSnapshot)
        assert snap.symbol == "BTC"
        assert snap.price >= 0
        assert snap.timestamp is not None

    def test_snapshot_24h_window_scales_with_timeframe(self):
        # 30 1h candles: real 24h window is the last 24 candles.
        df = _make_df(30, close_start=100.0, close_step=1.0)
        engine = LiveMarketEngine(collector=_MockCollector(df))
        snap = engine.snapshot(symbol="BTC", timeframe="1h", limit=30)
        # close[-24] = close[6] = 100 + 6 = 106; price = close[-1] = 129
        expected_change = round((129.0 - 106.0) / 106.0 * 100, 2)
        assert snap.change_24h == expected_change

    def test_snapshot_24h_window_for_4h_timeframe_uses_6_candles(self):
        # 4h candles: 24h = 6 candles, not 24. Use exactly 10 candles so the
        # buggy "always use last 24" path would fall back to summing/spanning
        # the whole series instead of just the real 6-candle 24h window.
        df = _make_df(10, close_start=100.0, close_step=1.0)
        engine = LiveMarketEngine(collector=_MockCollector(df))
        snap = engine.snapshot(symbol="BTC", timeframe="4h", limit=10)
        # close[-6] = close[4] = 104; price = close[-1] = 109
        expected_change = round((109.0 - 104.0) / 104.0 * 100, 2)
        assert snap.change_24h == expected_change
        # volume/high/low should be summed/maxed/minned over the last 6 candles only
        assert snap.volume_24h == 10.0 * 6
        assert snap.high_24h == round(float(df["high"].tail(6).max()), 2)
        assert snap.low_24h == round(float(df["low"].tail(6).min()), 2)
