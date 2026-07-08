"""Unit tests for PaperExecutor core logic (no external API dependencies)."""

import pytest
import pandas as pd

from database import Trade
from execution.paper_executor import PaperExecutor, PaperTradeRequest


class _MockCollector:
    def __init__(self, close_price=52000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


# ---------------------------------------------------------------------------
# _close_status_for_price
# ---------------------------------------------------------------------------

class TestCloseStatusForPrice:

    def _executor(self):
        return PaperExecutor(collector=_MockCollector(), session_factory=dict)

    def _trade(self, side="LONG", entry=50000.0, stop=49250.0, tp1=51000.0, tp2=None):
        return Trade(
            symbol="BTCUSDT", side=side, entry=entry,
            stop=stop, tp1=tp1, tp2=tp2, status="OPEN",
        )

    def test_long_tp_hit(self):
        e = self._executor()
        assert e._close_status_for_price(self._trade(), 51500.0) == "TP_HIT"

    def test_long_sl_hit(self):
        e = self._executor()
        assert e._close_status_for_price(self._trade(), 49000.0) == "SL_HIT"

    def test_long_no_close(self):
        e = self._executor()
        assert e._close_status_for_price(self._trade(), 50000.0) is None

    def test_long_exact_tp_boundary(self):
        e = self._executor()
        assert e._close_status_for_price(self._trade(tp1=51000.0), 51000.0) == "TP_HIT"

    def test_long_exact_sl_boundary(self):
        e = self._executor()
        assert e._close_status_for_price(self._trade(stop=49250.0), 49250.0) == "SL_HIT"

    def test_short_tp_hit(self):
        e = self._executor()
        t = self._trade(side="SHORT", entry=50000.0, stop=50750.0, tp1=49000.0)
        assert e._close_status_for_price(t, 48500.0) == "TP_HIT"

    def test_short_sl_hit(self):
        e = self._executor()
        t = self._trade(side="SHORT", entry=50000.0, stop=50750.0, tp1=49000.0)
        assert e._close_status_for_price(t, 51000.0) == "SL_HIT"

    def test_short_no_close(self):
        e = self._executor()
        t = self._trade(side="SHORT", entry=50000.0, stop=50750.0, tp1=49000.0)
        assert e._close_status_for_price(t, 50000.0) is None

    def test_short_exact_tp_boundary(self):
        e = self._executor()
        t = self._trade(side="SHORT", entry=50000.0, stop=50750.0, tp1=49000.0)
        assert e._close_status_for_price(t, 49000.0) == "TP_HIT"

    def test_short_exact_sl_boundary(self):
        e = self._executor()
        t = self._trade(side="SHORT", entry=50000.0, stop=50750.0, tp1=49000.0)
        assert e._close_status_for_price(t, 50750.0) == "SL_HIT"

    def test_missing_tp_sl_returns_none(self):
        e = self._executor()
        assert e._close_status_for_price(self._trade(tp1=None, stop=None), 99999.0) is None

    def test_long_tp2_hit(self):
        e = self._executor()
        assert e._close_status_for_price(self._trade(tp2=52000.0), 52500.0) == "TP_HIT"

    def test_long_tp2_before_tp1(self):
        e = self._executor()
        t = self._trade(tp1=51000.0, tp2=52000.0)
        assert e._close_status_for_price(t, 53000.0) == "TP_HIT"

    def test_long_tp1_still_triggers_when_tp2_not_set(self):
        e = self._executor()
        t = self._trade(tp1=51000.0, tp2=None)
        assert e._close_status_for_price(t, 51500.0) == "TP_HIT"

    def test_short_tp2_hit(self):
        e = self._executor()
        t = self._trade(side="SHORT", entry=50000.0, stop=50750.0, tp1=49000.0, tp2=48000.0)
        assert e._close_status_for_price(t, 47500.0) == "TP_HIT"


# ---------------------------------------------------------------------------
# _has_duplicate_position
# ---------------------------------------------------------------------------

class TestHasDuplicatePosition:

    def _executor(self):
        return PaperExecutor(collector=_MockCollector(), session_factory=dict)

    def test_duplicate_detected(self, db_session):
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", status="OPEN"))
        db_session.flush()
        assert self._executor()._has_duplicate_position(db_session, "BTCUSDT", "LONG") is True

    def test_no_duplicate(self, db_session):
        assert self._executor()._has_duplicate_position(db_session, "BTCUSDT", "LONG") is False

    def test_other_side_not_duplicate(self, db_session):
        db_session.add(Trade(symbol="BTCUSDT", side="SHORT", status="OPEN"))
        db_session.flush()
        assert self._executor()._has_duplicate_position(db_session, "BTCUSDT", "LONG") is False

    def test_closed_trade_not_duplicate(self, db_session):
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", status="TP_HIT"))
        db_session.flush()
        assert self._executor()._has_duplicate_position(db_session, "BTCUSDT", "LONG") is False


# ---------------------------------------------------------------------------
# _validate_trade_request
# ---------------------------------------------------------------------------

class TestValidateTradeRequest:

    def _executor(self):
        return PaperExecutor(collector=_MockCollector(), session_factory=dict)

    def test_long_valid(self):
        r = PaperTradeRequest(symbol="BTCUSDT", side="LONG", entry=50000.0, stop_loss=49250.0, take_profit=51000.0)
        self._executor()._validate_trade_request(r)

    def test_long_invalid_stop_above_entry(self):
        r = PaperTradeRequest(symbol="BTCUSDT", side="LONG", entry=50000.0, stop_loss=51000.0, take_profit=52000.0)
        with pytest.raises(ValueError, match="LONG trades require stop_loss < entry < take_profit"):
            self._executor()._validate_trade_request(r)

    def test_long_invalid_tp_below_entry(self):
        r = PaperTradeRequest(symbol="BTCUSDT", side="LONG", entry=50000.0, stop_loss=49000.0, take_profit=49500.0)
        with pytest.raises(ValueError, match="LONG trades require stop_loss < entry < take_profit"):
            self._executor()._validate_trade_request(r)

    def test_short_valid(self):
        r = PaperTradeRequest(symbol="BTCUSDT", side="SHORT", entry=50000.0, stop_loss=50750.0, take_profit=49000.0)
        self._executor()._validate_trade_request(r)

    def test_short_invalid_stop_below_entry(self):
        r = PaperTradeRequest(symbol="BTCUSDT", side="SHORT", entry=50000.0, stop_loss=49000.0, take_profit=48000.0)
        with pytest.raises(ValueError, match="SHORT trades require take_profit < entry < stop_loss"):
            self._executor()._validate_trade_request(r)

    def test_zero_entry_raises(self):
        r = PaperTradeRequest(symbol="BTCUSDT", side="LONG", entry=0.0, stop_loss=-100.0, take_profit=100.0)
        with pytest.raises(ValueError, match="entry must be greater than zero"):
            self._executor()._validate_trade_request(r)

    def test_empty_symbol_raises(self):
        r = PaperTradeRequest(symbol="", side="LONG", entry=50000.0, stop_loss=49250.0, take_profit=51000.0)
        with pytest.raises(ValueError, match="symbol is required"):
            self._executor()._validate_trade_request(r)

    def test_invalid_side_raises(self):
        r = PaperTradeRequest(symbol="BTCUSDT", side="INVALID", entry=50000.0, stop_loss=49250.0, take_profit=51000.0)
        with pytest.raises(ValueError, match="side must be LONG or SHORT"):
            self._executor()._validate_trade_request(r)

    def test_close_trade_positive_exit_price_succeeds(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        trade = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000.0,
            stop=49000.0, tp1=51000.0, status="OPEN",
        )
        db_session.add(trade)
        db_session.flush()

        executor = PaperExecutor(
            collector=_MockCollector(),
            session_factory=session_factory,
        )
        result = executor.close_trade(trade_id=trade.id, exit_price=52000.0)
        assert result is not None
        assert result.status == "CLOSED"

    def test_close_trade_none_exit_price_raises(self, session_factory):
        executor = PaperExecutor(
            collector=_MockCollector(),
            session_factory=session_factory,
        )
        with pytest.raises(ValueError, match="Invalid exit_price"):
            executor.close_trade(trade_id=1, exit_price=None)

    def test_close_trade_zero_exit_price_raises(self, session_factory):
        executor = PaperExecutor(
            collector=_MockCollector(),
            session_factory=session_factory,
        )
        with pytest.raises(ValueError, match="Invalid exit_price"):
            executor.close_trade(trade_id=1, exit_price=0.0)

    def test_close_trade_negative_exit_price_raises(self, session_factory):
        executor = PaperExecutor(
            collector=_MockCollector(),
            session_factory=session_factory,
        )
        with pytest.raises(ValueError, match="Invalid exit_price"):
            executor.close_trade(trade_id=1, exit_price=-1.0)


# ---------------------------------------------------------------------------
# SHORT trade monitoring
# ---------------------------------------------------------------------------

class TestMonitorShortTrade:

    def test_short_tp_hit(self, session_factory, db_session, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        db_session.add(Trade(
            symbol="BTCUSDT", side="SHORT",
            entry=50000.0, stop=50750.0, tp1=49000.0,
            status="OPEN",
        ))
        db_session.flush()

        executor = PaperExecutor(
            collector=_MockCollector(close_price=48000.0),
            session_factory=session_factory,
        )
        results = executor.monitor_open_trades()
        closed = [r for r in results if r.status == "TP_HIT"]
        assert len(closed) == 1
        assert closed[0].side == "SHORT"

    def test_short_sl_hit(self, session_factory, db_session, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        db_session.add(Trade(
            symbol="BTCUSDT", side="SHORT",
            entry=50000.0, stop=50750.0, tp1=49000.0,
            status="OPEN",
        ))
        db_session.flush()

        executor = PaperExecutor(
            collector=_MockCollector(close_price=51000.0),
            session_factory=session_factory,
        )
        results = executor.monitor_open_trades()
        closed = [r for r in results if r.status == "SL_HIT"]
        assert len(closed) == 1
        assert closed[0].side == "SHORT"


# ---------------------------------------------------------------------------
# PnL tracking dicts
# ---------------------------------------------------------------------------

class TestPnLTracking:

    def test_realized_pnl_and_percentages_accumulate(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )

        executor = PaperExecutor(
            collector=_MockCollector(close_price=52000.0),
            session_factory=session_factory,
        )

        trade_a = Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49250.0, tp1=51000.0, status="OPEN")
        trade_b = Trade(symbol="ETHUSDT", side="SHORT", entry=3000.0, stop=3090.0, tp1=2880.0, status="OPEN")
        db_session.add(trade_a)
        db_session.add(trade_b)
        db_session.flush()
        id_a = trade_a.id
        id_b = trade_b.id

        executor.close_trade(trade_id=id_a, exit_price=52000.0, status="TP_HIT")
        executor.close_trade(trade_id=id_b, exit_price=2800.0, status="TP_HIT")

        assert id_a in executor._realized_pnl
        assert id_b in executor._realized_pnl
        assert id_a in executor._pnl_percentages
        assert id_b in executor._pnl_percentages

        pnl_a = executor._realized_pnl[id_a]
        pnl_b = executor._realized_pnl[id_b]
        assert pnl_a > 0
        assert pnl_b > 0
        assert executor._pnl_percentages[id_a] > 0
        assert executor._pnl_percentages[id_b] > 0


# ---------------------------------------------------------------------------
# Notification failure during monitoring
# ---------------------------------------------------------------------------

class TestMonitorNotificationFailure:

    def test_monitor_does_not_fail_when_notification_raises(
        self, db_session, session_factory, monkeypatch,
    ):
        def raiser(*a, **kw):
            raise RuntimeError("emit failed")

        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            raiser,
        )

        trade = Trade(
            symbol="BTCUSDT", side="LONG",
            entry=50000.0, stop=49250.0, tp1=51000.0,
            status="OPEN",
        )
        db_session.add(trade)
        db_session.flush()

        executor = PaperExecutor(
            collector=_MockCollector(close_price=52000.0),
            session_factory=session_factory,
        )
        results = executor.monitor_open_trades()
        closed = [r for r in results if r.status == "TP_HIT"]
        assert len(closed) == 1


# ---------------------------------------------------------------------------
# Close trade validation
# ---------------------------------------------------------------------------

class TestCloseTradeValidation:

    def test_close_trade_invalid_status_raises(self, session_factory):
        executor = PaperExecutor(
            collector=_MockCollector(),
            session_factory=session_factory,
        )
        import pytest
        with pytest.raises(ValueError, match="close status must be one of"):
            executor.close_trade(trade_id=1, exit_price=50000.0, status="INVALID")

    def test_close_trade_already_closed_raises(self, db_session, session_factory, monkeypatch):
        from datetime import datetime, timezone
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        trade = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49250.0, tp1=51000.0,
            status="TP_HIT", exit_price=51000.0, closed_at=datetime.now(timezone.utc),
        )
        db_session.add(trade)
        db_session.flush()

        executor = PaperExecutor(
            collector=_MockCollector(),
            session_factory=session_factory,
        )
        with pytest.raises(ValueError, match="already in terminal status"):
            executor.close_trade(trade_id=trade.id, exit_price=52000.0, status="CLOSED")


class TestTP2Validation:

    def test_long_tp2_less_than_tp1_raises(self):
        executor = PaperExecutor(collector=_MockCollector(), session_factory=dict)
        from execution.paper_executor import PaperTradeRequest
        r = PaperTradeRequest(
            symbol="BTCUSDT", side="LONG", entry=50000.0,
            stop_loss=49000.0, take_profit=51000.0, take_profit_2=50500.0,
        )
        with pytest.raises(ValueError, match="stop < entry < tp1 < tp2"):
            executor._validate_trade_request(r)

    def test_short_tp2_greater_than_tp1_raises(self):
        executor = PaperExecutor(collector=_MockCollector(), session_factory=dict)
        from execution.paper_executor import PaperTradeRequest
        r = PaperTradeRequest(
            symbol="BTCUSDT", side="SHORT", entry=50000.0,
            stop_loss=51000.0, take_profit=49000.0, take_profit_2=49500.0,
        )
        with pytest.raises(ValueError, match="tp2 < tp1 < entry < stop"):
            executor._validate_trade_request(r)


class TestMonitorStaleTrade:

    def test_stale_trade_auto_closed(self, db_session, session_factory, monkeypatch):
        from datetime import datetime, timedelta, timezone
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        old = datetime.now(timezone.utc) - timedelta(days=30)
        trade = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49250.0, tp1=51000.0,
            status="OPEN", created_at=old,
        )
        db_session.add(trade)
        db_session.flush()

        executor = PaperExecutor(
            collector=_MockCollector(close_price=52000.0),
            session_factory=session_factory,
        )
        results = executor.monitor_open_trades()
        closed = [r for r in results if r.status == "CLOSED"]
        assert len(closed) == 1
        assert closed[0].realized_pnl is not None
