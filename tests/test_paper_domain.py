"""Unit tests for the paper trading domain (execution/paper.py)."""

import pytest
import pandas as pd

from database import (
    CANCEL,
    CLOSED,
    OPEN,
    TAKE_PROFIT,
    STOP_LOSS,
    Trade,
    PaperOrder as PaperOrderModel,
    PaperTrade as PaperTradeModel,
)
from execution.paper import PaperPosition, PaperOrder, PaperTrade, PaperExecutor


class _MockCollector:
    def __init__(self, close_price=52000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


# ---------------------------------------------------------------------------
# Domain model construction
# ---------------------------------------------------------------------------

class TestPaperPosition:

    def test_from_trade(self):
        trade = Trade(
            id=1, symbol="BTCUSDT", side="LONG", entry=50000.0,
            stop=49250.0, tp1=51000.0, tp2=52000.0, rr=2.0,
            pnl=100.0, status="OPEN",
        )
        pos = PaperPosition.from_trade(trade)
        assert pos.id == 1
        assert pos.symbol == "BTCUSDT"
        assert pos.side == "LONG"
        assert pos.entry == 50000.0
        assert pos.stop_loss == 49250.0
        assert pos.take_profit == 51000.0
        assert pos.take_profit_2 == 52000.0
        assert pos.pnl == 100.0
        assert pos.status == "OPEN"

    def test_from_trade_no_tp2(self):
        trade = Trade(
            id=2, symbol="ETHUSDT", side="SHORT", entry=3000.0,
            stop=3090.0, tp1=2880.0, tp2=None, rr=2.0,
            pnl=0.0, status="OPEN",
        )
        pos = PaperPosition.from_trade(trade)
        assert pos.take_profit_2 is None


class TestPaperOrder:

    def test_from_model(self):
        model = PaperOrderModel(
            id=10, symbol="BTCUSDT", side="LONG", order_type="MARKET",
            quantity=1.0, price=None, filled_price=50000.0, filled_quantity=1.0,
            status="FILLED", trade_id=5, reason=None,
        )
        order = PaperOrder.from_model(model)
        assert order.id == 10
        assert order.symbol == "BTCUSDT"
        assert order.side == "LONG"
        assert order.status == "FILLED"
        assert order.trade_id == 5


class TestPaperTrade:

    def test_from_model(self):
        model = PaperTradeModel(
            id=100, position_id=5, order_id=10,
            symbol="BTCUSDT", side="LONG", entry=50000.0,
            exit_price=None, quantity=1.0, pnl=0.0, status="OPEN",
            close_reason=None,
        )
        trade = PaperTrade.from_model(model)
        assert trade.id == 100
        assert trade.position_id == 5
        assert trade.symbol == "BTCUSDT"
        assert trade.status == "OPEN"


# ---------------------------------------------------------------------------
# PaperExecutor.place_order
# ---------------------------------------------------------------------------

class TestPlaceOrder:

    def test_place_order_creates_pending(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(
            position_executor=PaperExecutor._positions.__class__(
                collector=_MockCollector(),
                session_factory=session_factory,
            ) if hasattr(PaperExecutor, '_positions') else None,
        )
        # Actually, let me simplify — just use the default constructor with
        # monkeypatched session_factory for the order creation, and rely on
        # the existing monkeypatched get_session for the position executor.
        executor = PaperExecutor(session_factory=session_factory)
        # Override position_executor session_factory too
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="LONG", quantity=1.0,
        )
        assert order is not None
        assert order.status == "PENDING"
        assert order.symbol == "BTCUSDT"
        assert order.side == "LONG"

    def test_place_order_normalizes_symbol(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="  btcusdt  ", side=" long ", quantity=0.5,
        )
        assert order is not None
        assert order.symbol == "BTCUSDT"
        assert order.side == "LONG"

    def test_place_order_with_price(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="SHORT", quantity=2.0,
            order_type="LIMIT", price=49000.0, reason="test limit",
        )
        assert order is not None
        assert order.order_type == "LIMIT"
        assert order.price == 49000.0
        assert order.reason == "test limit"


# ---------------------------------------------------------------------------
# PaperExecutor.fill_order
# ---------------------------------------------------------------------------

class TestFillOrder:

    def test_fill_order_creates_position_and_trade(
        self, db_session, session_factory, monkeypatch,
    ):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="LONG", quantity=1.0,
        )
        assert order is not None

        result = executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )
        assert result is not None
        filled_order, position, trade = result

        assert filled_order.status == "FILLED"
        assert filled_order.filled_price == 50000.0
        assert filled_order.filled_quantity == 1.0
        assert filled_order.trade_id == position.id

        assert position.symbol == "BTCUSDT"
        assert position.side == "LONG"
        assert position.status == "OPEN"

        assert trade.position_id == position.id
        assert trade.order_id == order.id
        assert trade.symbol == "BTCUSDT"
        assert trade.status == "OPEN"

    def test_fill_nonexistent_order_returns_none(
        self, db_session, session_factory, monkeypatch,
    ):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        result = executor.fill_order(
            order_id=99999,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )
        assert result is None

    def test_fill_already_filled_order_returns_none(
        self, db_session, session_factory, monkeypatch,
    ):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="LONG", quantity=1.0,
        )
        assert order is not None

        result1 = executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )
        assert result1 is not None

        with pytest.raises(ValueError, match="already filled"):
            executor.fill_order(
                order_id=order.id,
                entry=51000.0,
                stop_loss=50250.0,
                take_profit=52000.0,
            )


# ---------------------------------------------------------------------------
# PaperExecutor.cancel_order
# ---------------------------------------------------------------------------

class TestCancelOrder:

    def test_cancel_pending_order(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="LONG", quantity=1.0,
        )
        assert order is not None

        cancelled = executor.cancel_order(order.id, reason="changed mind")
        assert cancelled is not None
        assert cancelled.status == CANCEL
        assert cancelled.reason == "changed mind"

    def test_cancel_nonexistent_order(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        result = executor.cancel_order(99999)
        assert result is None

    def test_cancel_filled_order_returns_none(
        self, db_session, session_factory, monkeypatch,
    ):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="LONG", quantity=1.0,
        )
        assert order is not None

        executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )

        with pytest.raises(ValueError, match="filled order cannot be cancelled"):
            executor.cancel_order(order.id)


# ---------------------------------------------------------------------------
# PaperExecutor.close_position
# ---------------------------------------------------------------------------

class TestClosePosition:

    def test_close_open_position(
        self, db_session, session_factory, monkeypatch,
    ):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="LONG", quantity=1.0,
        )
        assert order is not None

        result = executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )
        assert result is not None
        _, position, _ = result

        close_result = executor.close_position(
            trade_id=position.id,
            exit_price=52000.0,
            status=TAKE_PROFIT,
            close_reason="TP_HIT",
        )
        assert close_result is not None
        closed_position, closed_trade = close_result

        assert closed_position.status == TAKE_PROFIT
        assert closed_position.exit_price == 52000.0
        assert closed_trade is not None
        assert closed_trade.status == TAKE_PROFIT
        assert closed_trade.exit_price == 52000.0

    def test_close_position_without_trade_record(
        self, db_session, session_factory, monkeypatch,
    ):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        trade = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000.0,
            stop=49250.0, tp1=51000.0, status="OPEN",
        )
        db_session.add(trade)
        db_session.flush()
        trade_id = trade.id

        close_result = executor.close_position(
            trade_id=trade_id,
            exit_price=49000.0,
            status=STOP_LOSS,
            close_reason="SL_HIT",
        )
        assert close_result is not None
        closed_position, closed_trade = close_result
        assert closed_position.status == STOP_LOSS
        assert closed_trade is None


# ---------------------------------------------------------------------------
# PaperExecutor.getters
# ---------------------------------------------------------------------------

class TestGetters:

    def test_get_open_positions(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        assert executor.get_open_positions() == []

        db_session.add(Trade(
            symbol="BTCUSDT", side="LONG", entry=50000.0,
            stop=49250.0, tp1=51000.0, status="OPEN",
        ))
        db_session.flush()

        positions = executor.get_open_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "BTCUSDT"

    def test_get_orders(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        executor.place_order(symbol="BTCUSDT", side="LONG", quantity=1.0)
        executor.place_order(symbol="ETHUSDT", side="SHORT", quantity=2.0)

        orders = executor.get_orders()
        assert len(orders) == 2

        pending = executor.get_orders(status="PENDING")
        assert len(pending) == 2

    def test_get_trades(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        assert executor.get_trades() == []

        order = executor.place_order(symbol="BTCUSDT", side="LONG", quantity=1.0)
        assert order is not None

        result = executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )
        assert result is not None
        _, position, trade = result

        trades = executor.get_trades()
        assert len(trades) == 1

        trades_by_pos = executor.get_trades(position_id=position.id)
        assert len(trades_by_pos) == 1

        trades_by_status = executor.get_trades(status="OPEN")
        assert len(trades_by_status) == 1

        trades_by_bad_status = executor.get_trades(status="CLOSED")
        assert len(trades_by_bad_status) == 0


# ---------------------------------------------------------------------------
# CANCEL status constants
# ---------------------------------------------------------------------------

class TestCancelStatus:

    def test_cancel_status_constant(self):
        assert CANCEL == "CANCEL"
        assert CANCEL in {"TP_HIT", "SL_HIT", "CLOSED", "CANCEL"}

    def test_open_constant(self):
        assert OPEN == "OPEN"

    def test_close_constant(self):
        assert CLOSED == "CLOSED"


# ---------------------------------------------------------------------------
# SHORT trade lifecycle
# ---------------------------------------------------------------------------

class TestShortTradeLifecycle:

    def test_short_order_fill_and_close(
        self, db_session, session_factory, monkeypatch,
    ):
        monkeypatch.setattr(
            "execution.paper_executor.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )
        executor = PaperExecutor(session_factory=session_factory)
        executor._positions = executor._positions.__class__(
            collector=_MockCollector(),
            session_factory=session_factory,
        )

        order = executor.place_order(
            symbol="BTCUSDT", side="SHORT", quantity=1.0,
        )
        assert order is not None

        result = executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=50750.0,
            take_profit=49000.0,
        )
        assert result is not None
        _, position, trade = result

        assert position.side == "SHORT"
        assert trade.side == "SHORT"

        close_result = executor.close_position(
            trade_id=position.id,
            exit_price=48500.0,
            status=TAKE_PROFIT,
            close_reason="TP_HIT",
        )
        assert close_result is not None
        closed_position, closed_trade = close_result
        assert closed_position.status == TAKE_PROFIT
        assert closed_trade is not None
        assert closed_trade.status == TAKE_PROFIT
