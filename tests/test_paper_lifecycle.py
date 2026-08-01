"""Comprehensive lifecycle validation for the paper trading domain."""

import pytest
import pandas as pd

from database import (
    CANCEL,
    CLOSED,
    FILLED,
    OPEN,
    PARTIALLY_FILLED,
    PENDING,
    STOP_LOSS,
    TAKE_PROFIT,
    TRADE_FINAL_STATUSES,
    ORDER_FINAL_STATUSES,
    Trade,
    PaperOrder as PaperOrderModel,
    PaperTrade as PaperTradeModel,
)
from execution.lifecycle import (
    validate_order_transition,
    validate_trade_transition,
    validate_fill_order,
    validate_cancel_order,
    validate_close_trade,
    is_valid_order_transition,
    is_valid_trade_transition,
    is_order_terminal,
    is_trade_terminal,
)
from execution.paper import PaperExecutor


class _MockCollector:
    def __init__(self, close_price=52000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


# ===========================================================================
# Order lifecycle transitions
# ===========================================================================


class TestOrderTransitions:

    @pytest.mark.parametrize("current,new", [
        (PENDING, FILLED),
        (PENDING, PARTIALLY_FILLED),
        (PENDING, CANCEL),
        (PARTIALLY_FILLED, FILLED),
        (PARTIALLY_FILLED, CANCEL),
    ])
    def test_valid_transitions(self, current, new):
        validate_order_transition(current, new)

    @pytest.mark.parametrize("current,new", [
        (FILLED, CANCEL),
        (FILLED, PENDING),
        (FILLED, OPEN),
        (CANCEL, FILLED),
        (CANCEL, PENDING),
        (CANCEL, OPEN),
        (PENDING, OPEN),
        (PENDING, CLOSED),
        (PARTIALLY_FILLED, OPEN),
        (PARTIALLY_FILLED, PENDING),
    ])
    def test_invalid_transitions(self, current, new):
        with pytest.raises(ValueError):
            validate_order_transition(current, new)

    def test_terminal_filled_rejects_all(self):
        for target in [PENDING, FILLED, PARTIALLY_FILLED, CANCEL]:
            with pytest.raises(ValueError, match="terminal status"):
                validate_order_transition(FILLED, target)

    def test_terminal_cancel_rejects_all(self):
        for target in [PENDING, FILLED, PARTIALLY_FILLED, CANCEL]:
            with pytest.raises(ValueError, match="terminal status"):
                validate_order_transition(CANCEL, target)

    def test_unknown_current_status(self):
        with pytest.raises(ValueError, match="Unknown order status"):
            validate_order_transition("INVALID", FILLED)

    def test_unknown_new_status(self):
        with pytest.raises(ValueError, match="Unknown order status"):
            validate_order_transition(PENDING, "INVALID")


# ===========================================================================
# Trade lifecycle transitions
# ===========================================================================


class TestTradeTransitions:

    @pytest.mark.parametrize("current,new", [
        (OPEN, TAKE_PROFIT),
        (OPEN, STOP_LOSS),
        (OPEN, CLOSED),
        (OPEN, CANCEL),
    ])
    def test_valid_transitions(self, current, new):
        validate_trade_transition(current, new)

    @pytest.mark.parametrize("current,new", [
        (TAKE_PROFIT, CLOSED),
        (TAKE_PROFIT, OPEN),
        (TAKE_PROFIT, STOP_LOSS),
        (STOP_LOSS, CLOSED),
        (STOP_LOSS, OPEN),
        (STOP_LOSS, TAKE_PROFIT),
        (CLOSED, OPEN),
        (CLOSED, TAKE_PROFIT),
        (CANCEL, OPEN),
        (CANCEL, CLOSED),
    ])
    def test_invalid_transitions(self, current, new):
        with pytest.raises(ValueError):
            validate_trade_transition(current, new)

    @pytest.mark.parametrize("terminal", [TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL])
    def test_terminal_rejects_all_transitions(self, terminal):
        for target in [OPEN, TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL]:
            if target != terminal:
                with pytest.raises(ValueError, match="terminal status"):
                    validate_trade_transition(terminal, target)

    def test_unknown_current_status(self):
        with pytest.raises(ValueError, match="Unknown trade status"):
            validate_trade_transition("INVALID", CLOSED)

    def test_unknown_new_status(self):
        with pytest.raises(ValueError, match="Unknown trade status"):
            validate_trade_transition(OPEN, "INVALID")


# ===========================================================================
# validate_fill_order
# ===========================================================================


class TestValidateFillOrder:

    def test_pending_can_fill(self):
        validate_fill_order(PENDING)

    def test_partially_filled_can_fill(self):
        validate_fill_order(PARTIALLY_FILLED)

    def test_filled_raises(self):
        with pytest.raises(ValueError, match="already filled"):
            validate_fill_order(FILLED)

    def test_cancelled_raises(self):
        with pytest.raises(ValueError, match="cancelled order cannot be filled"):
            validate_fill_order(CANCEL)

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            validate_fill_order("INVALID")


# ===========================================================================
# validate_cancel_order
# ===========================================================================


class TestValidateCancelOrder:

    def test_pending_can_cancel(self):
        assert validate_cancel_order(PENDING) is True

    def test_partially_filled_can_cancel(self):
        assert validate_cancel_order(PARTIALLY_FILLED) is True

    def test_filled_raises(self):
        with pytest.raises(ValueError, match="filled order cannot be cancelled"):
            validate_cancel_order(FILLED)

    def test_already_cancelled_returns_false(self):
        assert validate_cancel_order(CANCEL) is False


# ===========================================================================
# validate_close_trade
# ===========================================================================


class TestValidateCloseTrade:

    @pytest.mark.parametrize("new", [TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL])
    def test_open_can_close(self, new):
        assert validate_close_trade(OPEN, new) is True

    def test_already_take_profit_returns_false(self):
        assert validate_close_trade(TAKE_PROFIT) is False

    def test_already_stop_loss_returns_false(self):
        assert validate_close_trade(STOP_LOSS) is False

    def test_already_closed_returns_false(self):
        assert validate_close_trade(CLOSED) is False

    def test_already_cancelled_returns_false(self):
        assert validate_close_trade(CANCEL) is False


# ===========================================================================
# Terminal status checks
# ===========================================================================


class TestTerminalStatus:

    @pytest.mark.parametrize("status", [FILLED, CANCEL])
    def test_order_terminal(self, status):
        assert is_order_terminal(status) is True

    @pytest.mark.parametrize("status", [PENDING, PARTIALLY_FILLED])
    def test_order_not_terminal(self, status):
        assert is_order_terminal(status) is False

    @pytest.mark.parametrize("status", [TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL])
    def test_trade_terminal(self, status):
        assert is_trade_terminal(status) is True

    @pytest.mark.parametrize("status", [OPEN])
    def test_trade_not_terminal(self, status):
        assert is_trade_terminal(status) is False


# ===========================================================================
# Idempotency — order cancel
# ===========================================================================


class TestCancelOrderIdempotent:

    def test_cancel_already_cancelled_returns_same_order(
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

        order = executor.place_order(symbol="BTCUSDT", side="LONG", quantity=1.0)
        assert order is not None

        first = executor.cancel_order(order.id, reason="test")
        assert first is not None
        assert first.status == CANCEL

        second = executor.cancel_order(order.id, reason="again")
        assert second is not None
        assert second.status == CANCEL

    def test_cancel_filled_order_raises(
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

        order = executor.place_order(symbol="BTCUSDT", side="LONG", quantity=1.0)
        assert order is not None

        executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )

        with pytest.raises(ValueError, match="filled order cannot be cancelled"):
            executor.cancel_order(order.id)

    def test_fill_cancelled_order_raises(
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

        order = executor.place_order(symbol="BTCUSDT", side="LONG", quantity=1.0)
        assert order is not None

        executor.cancel_order(order.id, reason="changed mind")

        with pytest.raises(ValueError, match="cancelled order cannot be filled"):
            executor.fill_order(
                order_id=order.id,
                entry=50000.0,
                stop_loss=49250.0,
                take_profit=51000.0,
            )

    def test_fill_already_filled_order_raises(
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

        order = executor.place_order(symbol="BTCUSDT", side="LONG", quantity=1.0)
        assert order is not None

        executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )

        with pytest.raises(ValueError, match="already filled"):
            executor.fill_order(
                order_id=order.id,
                entry=51000.0,
                stop_loss=50250.0,
                take_profit=52000.0,
            )


# ===========================================================================
# Idempotency — position close
# ===========================================================================


class TestClosePositionIdempotent:

    def test_close_already_closed_returns_same_position(
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

        order = executor.place_order(symbol="BTCUSDT", side="LONG", quantity=1.0)
        assert order is not None

        result = executor.fill_order(
            order_id=order.id,
            entry=50000.0,
            stop_loss=49250.0,
            take_profit=51000.0,
        )
        assert result is not None
        _, position, _ = result

        first = executor.close_position(
            trade_id=position.id,
            exit_price=52000.0,
            status=TAKE_PROFIT,
        )
        assert first is not None

        second = executor.close_position(
            trade_id=position.id,
            exit_price=53000.0,
            status=TAKE_PROFIT,
        )
        assert second is not None
        closed_position, _ = second
        assert closed_position.status == TAKE_PROFIT

    def test_close_position_transition_locked(
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
            stop=49250.0, tp1=51000.0, status="TP_HIT",
            exit_price=51000.0,
        )
        db_session.add(trade)
        db_session.flush()

        result = executor.close_position(
            trade_id=trade.id,
            exit_price=52000.0,
            status=CLOSED,
        )
        assert result is not None
        closed_position, _ = result
        assert closed_position.status == TAKE_PROFIT


# ===========================================================================
# Duplicate trade prevention
# ===========================================================================


class TestDuplicateTradePrevention:

    def test_has_open_trade_for_position_detects_duplicate(
        self, db_session, session_factory,
    ):
        trade = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000.0,
            stop=49250.0, tp1=51000.0, status="OPEN",
        )
        db_session.add(trade)
        db_session.flush()

        paper_trade = PaperTradeModel(
            position_id=trade.id,
            order_id=999,
            symbol="BTCUSDT",
            side="LONG",
            entry=50000.0,
            quantity=1.0,
            status=OPEN,
        )
        db_session.add(paper_trade)
        db_session.flush()

        result = PaperExecutor._has_open_trade_for_position(session_factory(), trade.id)
        assert result is True

    def test_has_open_trade_for_position_absent_returns_false(
        self, db_session, session_factory,
    ):
        result = PaperExecutor._has_open_trade_for_position(session_factory(), 9999)
        assert result is False


# ===========================================================================
# PARTIALLY_FILLED status
# ===========================================================================


class TestPartiallyFilled:

    def test_partially_filled_is_valid_order_status(self):
        validate_order_transition(PENDING, PARTIALLY_FILLED)
        validate_order_transition(PARTIALLY_FILLED, FILLED)
        validate_order_transition(PARTIALLY_FILLED, CANCEL)

    def test_partially_filled_not_terminal(self):
        assert is_order_terminal(PARTIALLY_FILLED) is False


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:

    def test_is_valid_helpers(self):
        assert is_valid_order_transition(PENDING, FILLED) is True
        assert is_valid_order_transition(FILLED, CANCEL) is False
        assert is_valid_trade_transition(OPEN, CLOSED) is True
        assert is_valid_trade_transition(CLOSED, OPEN) is False

    def test_close_position_without_paper_trade_succeeds(
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

        result = executor.close_position(
            trade_id=trade.id,
            exit_price=49000.0,
            status=STOP_LOSS,
        )
        assert result is not None
        pos, pt = result
        assert pos.status == STOP_LOSS
        assert pt is None

    def test_constants_defined(self):
        assert PENDING == "PENDING"
        assert FILLED == "FILLED"
        assert PARTIALLY_FILLED == "PARTIALLY_FILLED"
        assert CANCEL in ORDER_FINAL_STATUSES
        assert FILLED in ORDER_FINAL_STATUSES
        assert TAKE_PROFIT in TRADE_FINAL_STATUSES
        assert STOP_LOSS in TRADE_FINAL_STATUSES
        assert CLOSED in TRADE_FINAL_STATUSES
        assert CANCEL in TRADE_FINAL_STATUSES
