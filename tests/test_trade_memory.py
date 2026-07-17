from datetime import datetime, timezone

from decision.models import TradeOutcome, DecisionContext, DecisionSnapshot
from decision.trade_memory import TradeMemoryStore, TradeMemoryEntry


def make_outcome(symbol="BTC", side="LONG", pnl=1000.0, pnl_pct=2.0):
    return TradeOutcome(
        symbol=symbol,
        side=side,
        entry_price=50000.0,
        exit_price=51000.0 if pnl > 0 else 49000.0,
        pnl=pnl,
        pnl_pct=pnl_pct,
    )


class TestTradeMemoryEntry:

    def test_to_dict(self):
        entry = TradeMemoryEntry(
            symbol="BTC", side="LONG", entry_price=50000, exit_price=55000,
            pnl=5000, pnl_pct=10.0, is_win=True,
        )
        d = entry.to_dict()
        assert d["symbol"] == "BTC"
        assert d["is_win"] is True


class TestTradeMemoryStore:

    def test_store_outcome(self):
        store = TradeMemoryStore()
        outcome = make_outcome()
        entry = store.store(outcome)
        assert entry.symbol == "BTC"
        assert entry.is_win is True
        assert store.count() == 1

    def test_store_loss(self):
        store = TradeMemoryStore()
        outcome = make_outcome(pnl=-500.0, pnl_pct=-1.0)
        entry = store.store(outcome)
        assert entry.is_win is False
        assert entry.pnl == -500.0

    def test_find_by_symbol(self):
        store = TradeMemoryStore()
        store.store(make_outcome(symbol="BTC"))
        store.store(make_outcome(symbol="ETH"))
        results = store.find_by_symbol("BTC")
        assert len(results) == 1
        assert results[0].symbol == "BTC"

    def test_find_by_strategy(self):
        store = TradeMemoryStore()
        outcome = make_outcome()
        outcome.strategy_fingerprint = "trend_following"
        store.store(outcome)
        store.store(make_outcome(pnl=-200.0))
        results = store.find_by_strategy("trend_following")
        assert len(results) == 1

    def test_get_wins(self):
        store = TradeMemoryStore()
        store.store(make_outcome(pnl=100.0))
        store.store(make_outcome(pnl=-50.0))
        store.store(make_outcome(pnl=200.0))
        assert len(store.get_wins()) == 2
        assert len(store.get_losses()) == 1

    def test_win_rate(self):
        store = TradeMemoryStore()
        assert store.win_rate() == 0.0
        store.store(make_outcome(pnl=100.0))
        store.store(make_outcome(pnl=200.0))
        store.store(make_outcome(pnl=-50.0))
        assert store.win_rate() == 2.0 / 3.0

    def test_average_pnl(self):
        store = TradeMemoryStore()
        store.store(make_outcome(pnl=100.0))
        store.store(make_outcome(pnl=200.0))
        assert store.average_pnl() == 150.0

    def test_average_pnl_pct(self):
        store = TradeMemoryStore()
        store.store(make_outcome(pnl=100.0, pnl_pct=2.0))
        store.store(make_outcome(pnl=200.0, pnl_pct=4.0))
        assert store.average_pnl_pct() == 3.0

    def test_get_all(self):
        store = TradeMemoryStore()
        store.store(make_outcome())
        store.store(make_outcome(pnl=-50.0))
        assert len(store.get_all()) == 2

    def test_clear(self):
        store = TradeMemoryStore()
        store.store(make_outcome())
        store.clear()
        assert store.count() == 0

    def test_find_similar(self):
        store = TradeMemoryStore()
        store.store(make_outcome(symbol="BTC", side="LONG"))
        store.store(make_outcome(symbol="ETH", side="SHORT"))
        results = store.find_similar(symbol="BTC")
        assert len(results) == 1
        assert results[0].symbol == "BTC"

    def test_find_similar_combined(self):
        store = TradeMemoryStore()
        store.store(make_outcome(symbol="BTC", side="LONG"))
        store.store(make_outcome(symbol="BTC", side="SHORT"))
        results = store.find_similar(symbol="BTC", side="LONG")
        assert len(results) == 1

    def test_max_entries(self):
        store = TradeMemoryStore()
        store._max_entries = 5
        for i in range(10):
            store.store(make_outcome(pnl=float(i)))
        assert store.count() == 5

    def test_store_with_decision_snapshot(self):
        store = TradeMemoryStore()
        outcome = make_outcome()
        ctx = DecisionContext(signal_symbol="BTC", signal_side="LONG")
        snap = DecisionSnapshot(signal_id=1, decision="APPROVED", score=85.0, context=ctx)
        entry = store.store(outcome, decision_snapshot=snap)
        assert entry.decision_snapshot is not None
        assert entry.decision_snapshot["decision"] == "APPROVED"
