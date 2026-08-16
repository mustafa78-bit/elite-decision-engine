import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.websocket.manager import WebSocketManager
from database import UserSettings
from notifications.dispatcher import NotificationDispatcher, _persist_notification
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


def test_persist_notification_logs_instead_of_crashing_when_get_session_fails(monkeypatch, caplog):
    # get_session() itself raising (DB unreachable, pool exhausted) previously
    # left `session` unbound, so `finally: session.close()` raised a fresh
    # NameError that propagated out of emit() -- turning exactly the alert
    # meant to report a DB outage into an uncaught crash instead.
    def raiser():
        raise RuntimeError("db unreachable")

    monkeypatch.setattr("notifications.dispatcher.get_session", raiser)

    _persist_notification("SYSTEM_HEALTH_DEGRADED", {"component": "database"})

    assert "Failed to persist notification" in caplog.text


def test_emit_does_not_raise_when_persistence_is_totally_unavailable(monkeypatch):
    monkeypatch.setattr(
        "notifications.dispatcher.get_session",
        lambda: (_ for _ in ()).throw(RuntimeError("db unreachable")),
    )

    dispatcher = NotificationDispatcher()
    result = dispatcher.emit(TradeEvent.SYSTEM_HEALTH_DEGRADED, {"component": "database"})

    assert result["event"] == "SYSTEM_HEALTH_DEGRADED"


@pytest.mark.asyncio
async def test_dispatcher_broadcasts_via_websocket_manager():
    ws_manager = MagicMock(spec=WebSocketManager)
    ws_manager.broadcast_to_owner = AsyncMock()

    dispatcher = NotificationDispatcher(websocket_manager=ws_manager)

    result = dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {"symbol": "BTCUSDT", "side": "LONG"},
    )

    assert result["event"] == "TRADE_OPENED"
    assert result["payload"]["symbol"] == "BTCUSDT"

    # run_coroutine_threadsafe schedules via call_soon_threadsafe, an extra
    # hop beyond a plain Task -- a single sleep(0) isn't always enough to
    # let it run.
    await asyncio.sleep(0.05)
    ws_manager.broadcast_to_owner.assert_awaited_once()

    sent = json.loads(ws_manager.broadcast_to_owner.call_args[0][0])
    assert sent["event"] == "TRADE_OPENED"
    assert sent["payload"]["symbol"] == "BTCUSDT"
    # No "user_id" key in this payload -> owner_user_id arg is None,
    # matching the NULL-fallback (broadcast to everyone) convention.
    assert ws_manager.broadcast_to_owner.call_args[0][1] is None


def test_dispatcher_no_op_without_websocket_manager():
    dispatcher = NotificationDispatcher()

    result = dispatcher.emit(
        TradeEvent.TRADE_CLOSED,
        {"trade_id": 1, "pnl": 100.0},
    )

    assert result["event"] == "TRADE_CLOSED"
    assert result["payload"]["pnl"] == 100.0


def test_dispatcher_proactive_telegram_opened():
    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe = MagicMock()

    dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

    payload = {
        "trade_id": 42,
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry": 63250.50,
        "status": "OPEN",
    }
    result = dispatcher.emit(TradeEvent.TRADE_OPENED, payload)

    assert result["event"] == "TRADE_OPENED"
    mock_bot.send_alert_threadsafe.assert_called_once()
    alert_text = mock_bot.send_alert_threadsafe.call_args[0][0]
    assert "🟢 <b>TRADE OPENED</b>" in alert_text
    assert "BTCUSDT LONG" in alert_text
    assert "63250.5" in alert_text
    assert "ID: 42" in alert_text


def test_dispatcher_proactive_telegram_closed():
    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe = MagicMock()

    dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

    payload = {
        "trade_id": 42,
        "symbol": "ETHUSDT",
        "side": "SHORT",
        "exit_price": 3450.25,
        "pnl": 125.30,
        "close_reason": "TP_HIT",
    }
    result = dispatcher.emit(TradeEvent.TRADE_CLOSED, payload)

    assert result["event"] == "TRADE_CLOSED"
    mock_bot.send_alert_threadsafe.assert_called_once()
    alert_text = mock_bot.send_alert_threadsafe.call_args[0][0]
    assert "🔴 <b>TRADE CLOSED</b>" in alert_text
    assert "ETHUSDT SHORT" in alert_text
    assert "+125.30" in alert_text
    assert "TP_HIT" in alert_text
    assert "ID: 42" in alert_text


def test_dispatcher_telegram_failure_does_not_propagate():
    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe.side_effect = Exception("Telegram API Down")

    dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

    # Triggering emit should NOT raise an exception
    try:
        dispatcher.emit(
            TradeEvent.TRADE_OPENED,
            {"trade_id": 42, "symbol": "BTCUSDT", "side": "LONG", "entry": 60000},
        )
    except Exception as e:
        pytest.fail(f"Emit raised an exception on Telegram failure: {e}")


@pytest.mark.asyncio
async def test_dispatcher_telegram_to_thread_safety():
    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe = MagicMock()

    dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

    def background_work():
        dispatcher.emit(
            TradeEvent.TRADE_OPENED,
            {"trade_id": 100, "symbol": "SOLUSDT", "side": "LONG", "entry": 150},
        )

    await asyncio.to_thread(background_work)

    mock_bot.send_alert_threadsafe.assert_called_once()
    alert_text = mock_bot.send_alert_threadsafe.call_args[0][0]
    assert "SOLUSDT LONG" in alert_text


def test_dispatcher_unconfigured_telegram_no_ops():
    dispatcher = NotificationDispatcher(telegram_bot_manager=None)

    result = dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {"trade_id": 42, "symbol": "BTCUSDT", "side": "LONG", "entry": 60000},
    )
    assert result["event"] == "TRADE_OPENED"


@pytest.mark.asyncio
async def test_dispatcher_broadcasts_from_worker_thread():
    """emit() is called from inside asyncio.to_thread() by
    HealthService.check_and_alert() -- _broadcast() must still reach the
    websocket manager from there. Regression test: get_running_loop() raises
    RuntimeError in a worker thread with no loop of its own, which the old
    implementation silently swallowed, dropping the broadcast entirely.
    """
    ws_manager = MagicMock(spec=WebSocketManager)
    ws_manager.broadcast_to_owner = AsyncMock()

    dispatcher = NotificationDispatcher(websocket_manager=ws_manager)

    def background_work():
        dispatcher.emit(
            TradeEvent.SYSTEM_HEALTH_DEGRADED,
            {"component": "database", "status": "unhealthy"},
        )

    await asyncio.to_thread(background_work)
    await asyncio.sleep(0.05)

    ws_manager.broadcast_to_owner.assert_awaited_once()
    sent = json.loads(ws_manager.broadcast_to_owner.call_args[0][0])
    assert sent["event"] == "SYSTEM_HEALTH_DEGRADED"
    assert sent["payload"]["component"] == "database"


@pytest.mark.asyncio
async def test_dispatcher_scopes_broadcast_to_payload_user_id():
    ws_manager = MagicMock(spec=WebSocketManager)
    ws_manager.broadcast_to_owner = AsyncMock()

    dispatcher = NotificationDispatcher(websocket_manager=ws_manager)

    dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {"trade_id": 1, "user_id": 7, "symbol": "BTCUSDT", "side": "LONG"},
    )

    await asyncio.sleep(0.05)
    ws_manager.broadcast_to_owner.assert_awaited_once()
    assert ws_manager.broadcast_to_owner.call_args[0][1] == 7


def test_persist_notification_uses_payload_user_id_when_present(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("notifications.dispatcher.get_session", session_factory)

    from database import Notification

    _persist_notification(
        TradeEvent.TRADE_OPENED,
        {"trade_id": 1, "user_id": 42, "symbol": "BTCUSDT", "side": "LONG"},
    )

    notif = session_factory().query(Notification).filter_by(event_type="TRADE_OPENED").first()
    assert notif.user_id == 42


def test_persist_notification_falls_back_to_primary_user_without_payload_user_id(
    db_session, session_factory, monkeypatch
):
    monkeypatch.setattr("notifications.dispatcher.get_session", session_factory)

    from database import Notification

    _persist_notification("SYSTEM_HEALTH_DEGRADED", {"component": "database"})

    notif = session_factory().query(Notification).filter_by(event_type="SYSTEM_HEALTH_DEGRADED").first()
    assert notif.user_id == 1


def test_dispatcher_telegram_skipped_when_preference_disabled(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("notifications.dispatcher.get_session", session_factory)

    db_session.add(UserSettings(user_id=1, notification_preferences={"trade_opened": False}))
    db_session.commit()

    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe = MagicMock()
    dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

    result = dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {"trade_id": 1, "symbol": "BTCUSDT", "side": "LONG", "entry": 60000},
    )

    assert result["event"] == "TRADE_OPENED"
    mock_bot.send_alert_threadsafe.assert_not_called()


def test_dispatcher_telegram_sent_when_preference_enabled(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("notifications.dispatcher.get_session", session_factory)

    db_session.add(UserSettings(user_id=1, notification_preferences={"trade_opened": True, "trade_closed": False}))
    db_session.commit()

    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe = MagicMock()
    dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

    dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {"trade_id": 1, "symbol": "BTCUSDT", "side": "LONG", "entry": 60000},
    )

    mock_bot.send_alert_threadsafe.assert_called_once()


def test_dispatcher_telegram_defaults_enabled_without_user_settings_row(db_session, session_factory, monkeypatch):
    monkeypatch.setattr("notifications.dispatcher.get_session", session_factory)

    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe = MagicMock()
    dispatcher = NotificationDispatcher(telegram_bot_manager=mock_bot)

    dispatcher.emit(
        TradeEvent.TRADE_CLOSED,
        {"trade_id": 1, "symbol": "BTCUSDT", "side": "LONG", "pnl": 10.0},
    )

    mock_bot.send_alert_threadsafe.assert_called_once()


def test_dispatcher_disabled_telegram_preference_does_not_block_persistence_or_broadcast(
    db_session, session_factory, monkeypatch
):
    monkeypatch.setattr("notifications.dispatcher.get_session", session_factory)

    db_session.add(UserSettings(user_id=1, notification_preferences={"trade_opened": False}))
    db_session.commit()

    ws_manager = MagicMock(spec=WebSocketManager)
    ws_manager.broadcast_to_owner = AsyncMock()
    mock_bot = MagicMock()
    mock_bot.send_alert_threadsafe = MagicMock()

    dispatcher = NotificationDispatcher(websocket_manager=ws_manager, telegram_bot_manager=mock_bot)

    result = dispatcher.emit(
        TradeEvent.TRADE_OPENED,
        {"trade_id": 1, "symbol": "BTCUSDT", "side": "LONG", "entry": 60000},
    )

    assert result["event"] == "TRADE_OPENED"
    mock_bot.send_alert_threadsafe.assert_not_called()

    from database import Notification

    persisted = session_factory().query(Notification).filter_by(event_type="TRADE_OPENED").all()
    assert len(persisted) == 1
