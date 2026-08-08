import asyncio
import logging
from typing import Any, Optional

from api.websocket.manager import WebSocketManager
from database import Notification, get_session
from notifications.events import TradeEvent
from notifications.serializer import serialize_event

logger = logging.getLogger(__name__)


def _persist_notification(event: str, payload: dict) -> None:
    session = None
    try:
        session = get_session()
        notif = Notification(
            event_type=event,
            payload=payload,
        )
        session.add(notif)
        session.commit()
    except Exception as e:
        logger.warning("Failed to persist notification: %s", e)
    finally:
        if session is not None:
            session.close()


class NotificationDispatcher:

    def __init__(
        self,
        websocket_manager: WebSocketManager | None = None,
        telegram_bot_manager: Any | None = None,
    ) -> None:
        self.websocket_manager = websocket_manager
        if telegram_bot_manager is None:
            try:
                from services.telegram.bot import TelegramBotManager
                self.telegram_bot_manager = TelegramBotManager.get_instance()
            except ImportError:
                self.telegram_bot_manager = None
        else:
            self.telegram_bot_manager = telegram_bot_manager

        # Captured so _broadcast() can hand off to this loop from a worker
        # thread (e.g. emit() called inside asyncio.to_thread(), as
        # HealthService.check_and_alert() does) -- None if constructed
        # outside any running loop (e.g. a sync test), matching how
        # websocket_manager=None already disables broadcasting.
        try:
            self._loop: asyncio.AbstractEventLoop | None = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def emit(self, event, payload):
        logger.info(
            "Notification event: %s | payload=%s",
            event,
            payload,
        )

        message = serialize_event(event, payload)

        _persist_notification(event, payload)

        if self.websocket_manager is not None:
            self._broadcast(message)

        # Trigger proactive Telegram alert if configured
        proactive_events = (
            TradeEvent.TRADE_OPENED,
            TradeEvent.TRADE_CLOSED,
            TradeEvent.SYSTEM_HEALTH_DEGRADED,
            TradeEvent.SYSTEM_HEALTH_RECOVERED,
        )
        if event in proactive_events and self.telegram_bot_manager is not None:
            try:
                msg = ""
                if event == TradeEvent.TRADE_OPENED:
                    trade_id = payload.get("trade_id")
                    symbol = payload.get("symbol", "UNKNOWN")
                    side = payload.get("side", "UNKNOWN")
                    entry = payload.get("entry")
                    msg = f"🟢 <b>TRADE OPENED</b>\n<b>{symbol} {side}</b> @ {entry}\nID: {trade_id}"
                elif event == TradeEvent.TRADE_CLOSED:
                    trade_id = payload.get("trade_id")
                    symbol = payload.get("symbol", "UNKNOWN")
                    side = payload.get("side", "UNKNOWN")
                    exit_price = payload.get("exit_price")
                    pnl_val = payload.get("pnl")
                    close_reason = payload.get("close_reason") or payload.get("status", "CLOSED")

                    pnl_str = "N/A"
                    if pnl_val is not None:
                        try:
                            pnl_float = float(pnl_val)
                            pnl_prefix = "+" if pnl_float > 0 else ""
                            pnl_str = f"{pnl_prefix}{pnl_float:.2f}"
                        except (ValueError, TypeError):
                            pnl_str = str(pnl_val)

                    msg = f"🔴 <b>TRADE CLOSED</b>\n<b>{symbol} {side}</b>\nExit Price: {exit_price}\nPnL: {pnl_str}\nReason: {close_reason}\nID: {trade_id}"
                elif event == TradeEvent.SYSTEM_HEALTH_DEGRADED:
                    component = payload.get("component", "UNKNOWN")
                    status = payload.get("status", "unknown")
                    detail = payload.get("detail")
                    detail_line = f"\nDetail: {detail}" if detail else ""
                    msg = f"⚠️ <b>SYSTEM HEALTH DEGRADED</b>\nComponent: <b>{component}</b>\nStatus: {status}{detail_line}"
                else:  # SYSTEM_HEALTH_RECOVERED
                    component = payload.get("component", "UNKNOWN")
                    msg = f"✅ <b>SYSTEM HEALTH RECOVERED</b>\nComponent: <b>{component}</b> is healthy again"

                self.telegram_bot_manager.send_alert_threadsafe(msg)
            except Exception as e:
                logger.warning("Failed to prepare or trigger Telegram alert: %s", e)

        return {
            "event": event,
            "payload": payload,
        }

    def _broadcast(self, message: str) -> None:
        # emit() (and therefore this) can run inside a worker thread with no
        # running loop of its own -- asyncio.get_running_loop() would raise
        # there, which the old code silently swallowed, dropping the
        # broadcast entirely. run_coroutine_threadsafe() against the loop
        # captured at construction time works from any thread.
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self.websocket_manager.broadcast(message), self._loop
        )
