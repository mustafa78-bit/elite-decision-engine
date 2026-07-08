"""Tests for live market data engine."""

from market_data.live.engine import LiveMarketEngine, MarketSnapshot


class TestMarketSnapshot:
    def test_snapshot_returns_snapshot(self):
        engine = LiveMarketEngine()
        snap = engine.snapshot(symbol="BTC")
        assert isinstance(snap, MarketSnapshot)
        assert snap.symbol == "BTC"
        assert snap.price >= 0
        assert snap.timestamp is not None
