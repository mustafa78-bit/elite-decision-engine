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
