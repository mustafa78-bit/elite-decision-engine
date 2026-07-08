import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.websocket.manager import WebSocketManager
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


@pytest.mark.asyncio
async def test_dispatcher_broadcasts_via_websocket_manager():
    ws_manager = MagicMock(spec=WebSocketManager)
    ws_manager.broadcast = AsyncMock()

    dispatcher = NotificationDispatcher(websocket_manager=ws_manager)

    result = dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {"symbol": "BTCUSDT", "side": "LONG"},
    )

    assert result["event"] == "TRADE_OPENED"
    assert result["payload"]["symbol"] == "BTCUSDT"

    await asyncio.sleep(0)
    ws_manager.broadcast.assert_awaited_once()

    sent = json.loads(ws_manager.broadcast.call_args[0][0])
    assert sent["event"] == "TRADE_OPENED"
    assert sent["payload"]["symbol"] == "BTCUSDT"


def test_dispatcher_no_op_without_websocket_manager():
    dispatcher = NotificationDispatcher()

    result = dispatcher.emit(
        TradeEvent.TRADE_CLOSED,
        {"trade_id": 1, "pnl": 100.0},
    )

    assert result["event"] == "TRADE_CLOSED"
    assert result["payload"]["pnl"] == 100.0
