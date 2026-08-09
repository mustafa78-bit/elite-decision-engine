"""Proves TRADE_OPENED/TRADE_CLOSED actually reach the real WebSocketManager
when TradeEngine/PaperExecutor are wired the way api/main.py's lifespan()
constructs them in production.

Previously, api/main.py's lifespan() constructed ExecutionLoop with no
trade_engine=/paper_executor= override, so TradeEngine/PaperExecutor each
default-constructed their own private NotificationDispatcher() with
websocket_manager=None -- trade events were persisted to DB and sent to
Telegram, but self.websocket_manager is not None was always False, so
_broadcast() never ran for them. The only websocket-wired dispatcher
anywhere was _health_monitor_loop()'s own separate instance, used only for
SYSTEM_HEALTH_* events.
(SPRINT_JULES_TRADE_WEBSOCKET_NOTIFICATIONS_DEAD_IN_PRODUCTION.md)

Fix: one shared NotificationDispatcher(websocket_manager=manager),
constructed once in lifespan() and passed into TradeEngine(notifications=...),
PaperExecutor(notifications=...), and _health_monitor_loop(dispatcher).
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.websocket.manager import WebSocketManager
from database import Signal
from execution.paper_executor import PaperExecutor
from execution.trade_engine import TradeEngine
from notifications.dispatcher import NotificationDispatcher


@pytest.mark.asyncio
async def test_trade_engine_broadcasts_trade_opened_via_shared_dispatcher(db_session):
    # Mirrors exactly how api/main.py's lifespan() wires things: one shared
    # dispatcher constructed with a real websocket_manager, injected into
    # TradeEngine -- not TradeEngine's own default-constructed dispatcher.
    ws_manager = MagicMock(spec=WebSocketManager)
    ws_manager.broadcast = AsyncMock()
    shared_dispatcher = NotificationDispatcher(websocket_manager=ws_manager)

    engine = TradeEngine(notifications=shared_dispatcher)

    signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()

    trade = engine.create_trade(signal=signal, entry=50000.0, atr=500.0)
    assert trade is not None

    await asyncio.sleep(0.05)
    ws_manager.broadcast.assert_awaited_once()
    sent = json.loads(ws_manager.broadcast.call_args[0][0])
    assert sent["event"] == "TRADE_OPENED"
    assert sent["payload"]["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_paper_executor_broadcasts_trade_closed_via_shared_dispatcher(db_session, session_factory):
    from database import PaperTrade, Trade

    ws_manager = MagicMock(spec=WebSocketManager)
    ws_manager.broadcast = AsyncMock()
    shared_dispatcher = NotificationDispatcher(websocket_manager=ws_manager)

    executor = PaperExecutor(session_factory=session_factory, notifications=shared_dispatcher)

    trade = Trade(
        symbol="ETHUSDT", side="LONG", entry=3000.0, status="OPEN",
        stop=2900.0, tp1=3200.0,
    )
    db_session.add(trade)
    db_session.flush()
    pt = PaperTrade(
        position_id=trade.id, symbol="ETHUSDT", side="LONG",
        entry=3000.0, quantity=1.0, status="OPEN",
    )
    db_session.add(pt)
    db_session.commit()

    executor.close_trade(trade.id, exit_price=3100.0, close_reason="MANUAL_CLOSE")

    await asyncio.sleep(0.05)
    ws_manager.broadcast.assert_awaited()
    events = [json.loads(c.args[0])["event"] for c in ws_manager.broadcast.await_args_list]
    assert "TRADE_CLOSED" in events


def test_default_constructed_trade_engine_and_paper_executor_have_no_websocket_manager():
    # Regression guard: confirms the *bug's* precondition still holds when no
    # dispatcher is explicitly injected -- default construction stays
    # websocket-less, which is exactly why api/main.py's lifespan() must
    # inject a shared one explicitly rather than relying on the default.
    assert TradeEngine().notifications.websocket_manager is None
    assert PaperExecutor().notifications.websocket_manager is None
