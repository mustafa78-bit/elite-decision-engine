from notifications.dispatcher import NotificationDispatcher
from notifications.events import TradeEvent


def test_notification_dispatcher_emit():

    dispatcher = NotificationDispatcher()

    result = dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {
            "symbol": "BTCUSDT",
            "side": "LONG",
        },
    )

    assert result["event"] == "TRADE_OPENED"
    assert result["payload"]["symbol"] == "BTCUSDT"
