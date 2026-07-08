"""Tests for trade memory system."""

from memory.trade_memory import TradeMemory, TradeMemoryEntry


class TestTradeMemory:
    def test_record(self, session_factory):
        mem = TradeMemory(session_factory=session_factory)
        mid = mem.record("BTC", "LONG", 50000.0, "Bullish breakout", conditions={"rsi": 65, "trend": "BULLISH"})
        assert mid > 0
        entry = mem.get(mid)
        assert entry is not None
        assert entry.symbol == "BTC"
        assert entry.side == "LONG"
        assert entry.entry_price == 50000.0

    def test_record_with_tags(self, session_factory):
        mem = TradeMemory(session_factory=session_factory)
        mid = mem.record("ETH", "SHORT", 3000.0, "RSI overbought", tags=["rsi", "overbought"])
        entry = mem.get(mid)
        assert entry is not None
        assert "rsi" in entry.tags
        assert "overbought" in entry.tags

    def test_close(self, session_factory):
        mem = TradeMemory(session_factory=session_factory)
        mid = mem.record("BTC", "LONG", 50000.0, "Breakout")
        result = mem.close(mid, exit_price=55000.0, pnl=5000.0, result="WIN", exit_reason="TP_HIT", lessons=["Wait for confirmation"])
        assert result is True
        entry = mem.get(mid)
        assert entry.result == "WIN"
        assert entry.pnl == 5000.0
        assert entry.exit_price == 55000.0
        assert "Wait for confirmation" in entry.lessons

    def test_close_nonexistent(self, session_factory):
        mem = TradeMemory(session_factory=session_factory)
        assert mem.close(99999, 100, 0, "LOSS") is False

    def test_get_nonexistent(self, session_factory):
        mem = TradeMemory(session_factory=session_factory)
        assert mem.get(99999) is None

    def test_list(self, session_factory):
        mem = TradeMemory(session_factory=session_factory)
        mem.record("BTC", "LONG", 100, "reason1")
        mem.record("ETH", "SHORT", 200, "reason2")
        entries = mem.list()
        assert len(entries) >= 2

    def test_stats(self, session_factory):
        mem = TradeMemory(session_factory=session_factory)
        mid1 = mem.record("BTC", "LONG", 100, "r1")
        mid2 = mem.record("ETH", "SHORT", 200, "r2")
        mem.close(mid1, 150, 50, "WIN")
        mem.close(mid2, 180, -20, "LOSS")
        stats = mem.stats()
        assert stats["total_entries"] >= 2
        assert stats["wins"] >= 1
        assert stats["losses"] >= 1
        assert stats["win_rate_pct"] > 0
