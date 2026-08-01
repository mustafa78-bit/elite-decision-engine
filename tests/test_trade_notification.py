from unittest.mock import MagicMock

from database import Signal
from execution.trade_engine import TradeEngine


def test_trade_engine_emits_trade_opened_notification(db_session, monkeypatch):
    """Verify that TradeEngine.create_trade emits TRADE_OPENED notification."""

    signal = Signal(
        symbol="BTCUSDT",
        side="LONG",
        timeframe="1h",
        status="OPEN",
    )
    db_session.add(signal)
    db_session.flush()

    mock_emit = MagicMock()
    monkeypatch.setattr(
        "execution.trade_engine.NotificationDispatcher.emit",
        mock_emit,
    )

    engine = TradeEngine()
    trade = engine.create_trade(
        signal=signal,
        entry=50000.0,
        atr=500.0,
    )

    assert trade is not None
    mock_emit.assert_called_once()

    args, _ = mock_emit.call_args
    event, payload = args[0], args[1]

    assert event == "TRADE_OPENED"
    assert payload["trade_id"] == trade.id
    assert payload["symbol"] == "BTCUSDT"
    assert payload["side"] == "LONG"
    assert payload["entry"] == 50000.0
    assert payload["status"] == "OPEN"


def test_trade_engine_emits_intelligence_in_payload(db_session, monkeypatch):
    """Verify that TRADE_OPENED payload includes intelligence data."""

    signal = Signal(
        symbol="ETHUSDT",
        side="SHORT",
        timeframe="1h",
        status="OPEN",
    )
    db_session.add(signal)
    db_session.flush()

    mock_emit = MagicMock()
    monkeypatch.setattr(
        "execution.trade_engine.NotificationDispatcher.emit",
        mock_emit,
    )

    engine = TradeEngine()
    intelligence = {
        "confidence": 92.5,
        "decision": "STRONG_APPROVE",
        "final_score": 0.95,
        "trend_score": 0.8,
    }
    trade = engine.create_trade(
        signal=signal,
        entry=3000.0,
        atr=50.0,
        intelligence=intelligence,
    )

    assert trade is not None
    args, _ = mock_emit.call_args
    _, payload = args[0], args[1]

    assert "intelligence" in payload
    assert payload["intelligence"]["confidence"] == 92.5
    assert payload["intelligence"]["decision"] == "STRONG_APPROVE"
    assert payload["intelligence"]["final_score"] == 0.95


def test_trade_engine_intelligence_defaults_to_empty_dict(db_session, monkeypatch):
    """Verify that intelligence defaults to {} when not provided."""

    signal = Signal(
        symbol="BTCUSDT",
        side="LONG",
        timeframe="1h",
        status="OPEN",
    )
    db_session.add(signal)
    db_session.flush()

    mock_emit = MagicMock()
    monkeypatch.setattr(
        "execution.trade_engine.NotificationDispatcher.emit",
        mock_emit,
    )

    engine = TradeEngine()
    trade = engine.create_trade(
        signal=signal,
        entry=50000.0,
        atr=500.0,
    )

    assert trade is not None
    args, _ = mock_emit.call_args
    _, payload = args[0], args[1]

    assert "intelligence" in payload
    assert payload["intelligence"] == {}
