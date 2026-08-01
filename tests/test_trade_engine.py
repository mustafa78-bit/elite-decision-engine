"""Unit tests for TradeEngine error handling and edge cases."""

from database import Signal
from execution.trade_engine import TradeEngine


class TestTradeEngine:

    def test_duplicate_signal_returns_existing(self, db_session):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        engine = TradeEngine()
        first = engine.create_trade(signal=signal, entry=50000.0, atr=500.0)
        assert first is not None

        second = engine.create_trade(signal=signal, entry=50000.0, atr=500.0)
        assert second is not None
        assert second.id == first.id

    def test_create_trade_populates_all_levels(self, db_session):
        signal = Signal(symbol="ETHUSDT", side="SHORT", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        trade = TradeEngine().create_trade(signal=signal, entry=3000.0, atr=60.0)
        assert trade is not None
        assert trade.symbol == "ETHUSDT"
        assert trade.side == "SHORT"
        assert trade.entry == 3000.0
        assert trade.stop == 3090.0
        assert trade.tp1 == 2880.0
        assert trade.tp2 == 2760.0
        assert abs(trade.rr - 1.33) < 0.01
        assert trade.status == "OPEN"

    def test_none_on_notification_failure(self, db_session, monkeypatch):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        def raiser(*a, **kw):
            raise RuntimeError("emit failed")

        monkeypatch.setattr(
            "execution.trade_engine.NotificationDispatcher.emit",
            raiser,
        )

        trade = TradeEngine().create_trade(signal=signal, entry=50000.0, atr=500.0)
        assert trade is None

    def test_same_symbol_side_duplicate_returns_none(self, db_session):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        engine = TradeEngine()
        first = engine.create_trade(signal=signal, entry=50000.0, atr=500.0)
        assert first is not None

        signal.id = None
        second = engine.create_trade(signal=signal, entry=50000.0, atr=500.0)
        assert second is None

    def test_create_trade_zero_entry_returns_none(self, db_session, monkeypatch):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        monkeypatch.setattr(
            "execution.trade_engine.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )

        trade = TradeEngine().create_trade(signal=signal, entry=0.0, atr=500.0)
        assert trade is None
