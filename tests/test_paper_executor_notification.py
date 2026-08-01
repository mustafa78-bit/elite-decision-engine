from unittest.mock import MagicMock

import pandas as pd

from database import Trade
from execution.paper_executor import PaperExecutor


class _MockCollector:
    def __init__(self, close_price=52000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


def test_close_trade_emits_trade_closed(db_session, session_factory, monkeypatch):
    """PaperExecutor.close_trade emits TRADE_CLOSED notification."""

    trade = Trade(
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49250.0,
        tp1=51000.0,
        status="OPEN",
    )
    db_session.add(trade)
    db_session.flush()
    trade_id = trade.id

    mock_emit = MagicMock()
    monkeypatch.setattr(
        "execution.paper_executor.NotificationDispatcher.emit",
        mock_emit,
    )

    executor = PaperExecutor(session_factory=session_factory)
    result = executor.close_trade(
        trade_id=trade_id,
        exit_price=52000.0,
        status="TP_HIT",
    )

    assert result is not None
    mock_emit.assert_called_once()
    args, _ = mock_emit.call_args
    event, payload = args[0], args[1]

    assert event == "TRADE_CLOSED"
    assert payload["trade_id"] == trade_id
    assert payload["symbol"] == "BTCUSDT"
    assert payload["side"] == "LONG"
    assert payload["status"] == "TP_HIT"
    assert payload["exit_price"] == 52000.0
    assert payload["close_reason"] == "TP_HIT"


def test_monitor_trade_emits_trade_closed_on_tp_hit(
    db_session, session_factory, monkeypatch,
):
    """monitor_open_trades emits TRADE_CLOSED when TP is hit."""

    trade = Trade(
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49250.0,
        tp1=51000.0,
        status="OPEN",
    )
    db_session.add(trade)
    db_session.flush()

    mock_emit = MagicMock()
    monkeypatch.setattr(
        "execution.paper_executor.NotificationDispatcher.emit",
        mock_emit,
    )

    executor = PaperExecutor(
        collector=_MockCollector(close_price=52000.0),
        session_factory=session_factory,
    )
    results = executor.monitor_open_trades()

    closed = [r for r in results if r.status == "TP_HIT"]
    assert len(closed) == 1

    mock_emit.assert_called_once()
    args, _ = mock_emit.call_args
    event, payload = args[0], args[1]

    assert event == "TRADE_CLOSED"
    assert payload["trade_id"] == trade.id
    assert payload["symbol"] == "BTCUSDT"
    assert payload["side"] == "LONG"
    assert payload["status"] == "TP_HIT"
    assert payload["close_reason"] == "TP_HIT"
