import asyncio
import logging
from datetime import datetime
from typing import Any

from api.websocket.manager import WebSocketManager
from database import Notification, UserSettings, get_session
from notifications.events import TradeEvent
from notifications.serializer import serialize_event

logger = logging.getLogger(__name__)

# Maps an event to the notification_preferences key that gates its proactive
# Telegram alert. DB persistence and websocket broadcast stay unconditional
# for every event -- only the interruptive Telegram push is gated, so the
# notification center's history always stays complete regardless of alert
# preferences.
_TELEGRAM_PREFERENCE_KEY_BY_EVENT = {
    TradeEvent.TRADE_OPENED: "trade_opened",
    TradeEvent.TRADE_CLOSED: "trade_closed",
    TradeEvent.SYSTEM_HEALTH_DEGRADED: "system_alert",
    TradeEvent.SYSTEM_HEALTH_RECOVERED: "system_alert",
}

# Telegram alerting is single-tenant today: TELEGRAM_CHAT_ID is one global
# config value, not per-user chat routing (no multi-recipient support exists
# anywhere in this app). Preferences are gated against this one primary
# account's settings rather than inventing per-user routing the rest of the
# app doesn't support yet -- revisit if/when real multi-user Telegram
# delivery is built.
_PRIMARY_USER_ID = 1


def _telegram_alert_enabled(event: str) -> bool:
    key = _TELEGRAM_PREFERENCE_KEY_BY_EVENT.get(event)
    if key is None:
        return True
    session = None
    try:
        session = get_session()
        settings = session.query(UserSettings).filter(UserSettings.user_id == _PRIMARY_USER_ID).first()
    except Exception as e:
        logger.warning("Failed to load notification preferences, defaulting to enabled: %s", e)
        return True
    finally:
        if session is not None:
            session.close()
    if settings is None or not settings.notification_preferences:
        return True
    return settings.notification_preferences.get(key, True)


def _risk_reward_ratio(entry, stop, target) -> str | None:
    if not entry or not stop or not target:
        return None
    risk = abs(entry - stop)
    if risk == 0:
        return None
    reward = abs(target - entry)
    return f"1:{reward / risk:.2f}"


def _format_opened_at(payload: dict) -> str | None:
    raw = payload.get("opened_at")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).strftime("%d.%m.%Y %H:%M UTC")
    except (ValueError, TypeError):
        return None


def _build_trade_opened_caption(payload: dict) -> str:
    trade_id = payload.get("trade_id")
    symbol = payload.get("symbol", "UNKNOWN")
    side = str(payload.get("side", "UNKNOWN")).upper()
    entry = payload.get("entry")
    stop = payload.get("stop")
    tp1 = payload.get("tp1")
    tp2 = payload.get("tp2")
    intel = payload.get("intelligence") or {}

    levels_lines = [f"Giriş: {entry}"]
    if stop:
        levels_lines.append(f"Stop: {stop}")
    if tp1:
        rr1 = _risk_reward_ratio(entry, stop, tp1)
        levels_lines.append(f"TP1: {tp1}" + (f" (R:R {rr1})" if rr1 else ""))
    if tp2:
        rr2 = _risk_reward_ratio(entry, stop, tp2)
        levels_lines.append(f"TP2: {tp2}" + (f" (R:R {rr2})" if rr2 else ""))
    opened_at = _format_opened_at(payload)
    if opened_at:
        levels_lines.append(f"Zaman: {opened_at}")
    levels_block = "\n".join(levels_lines)

    # "Neden LONG/SHORT" -- the same component scores ScoringEngine.score()
    # and ConfidenceEngine.calculate() used to approve this trade
    # (execution/execution_loop.py's _create_trade() threads them through as
    # `intelligence`), surfaced so the alert answers "why this side" instead
    # of just announcing the fact of the trade.
    reason_line = None
    score_keys = ("trend_score", "volume_score", "btc_score", "mtf_score", "risk_score")
    if any(k in intel for k in score_keys):
        parts = []
        labels = {
            "trend_score": "Trend", "volume_score": "Hacim", "btc_score": "BTC Sağlığı",
            "mtf_score": "MTF", "risk_score": "Risk",
        }
        for key in score_keys:
            if key in intel:
                parts.append(f"{labels[key]} {intel[key]}/1.0")
        reason_line = " · ".join(parts)

    summary_bits = []
    if "final_score" in intel:
        summary_bits.append(f"Final Skor: {intel['final_score']}")
    if "confidence" in intel:
        summary_bits.append(f"Güven: %{intel['confidence']}")
    if "decision" in intel:
        summary_bits.append(f"({intel['decision']})")
    summary_line = " | ".join(summary_bits) if summary_bits else None

    reason_block = ""
    if reason_line or summary_line:
        reason_block = f"\n\n<b>Neden {side}:</b>"
        if reason_line:
            reason_block += f"\n{reason_line}"
        if summary_line:
            reason_block += f"\n{summary_line}"

    return (
        f"🟢 <b>İŞLEM AÇILDI</b>\n"
        f"<b>{symbol} {side}</b> @ {entry}\n\n"
        f"{levels_block}"
        f"{reason_block}\n\n"
        f"ID: {trade_id}"
    )


def _trade_opened_chart_kwargs(payload: dict) -> dict:
    # Passed through to services.telegram.chart_screenshot.capture_trade_chart_png()
    # (imported lazily there -- this module has no direct Playwright dependency).
    return {
        "symbol": payload.get("symbol") or "",
        "timeframe": payload.get("timeframe") or "1h",
        "side": str(payload.get("side", "")),
        "entry": payload.get("entry"),
        "stop": payload.get("stop"),
        "tp1": payload.get("tp1"),
        "tp2": payload.get("tp2"),
    }


def _persist_notification(event: str, payload: dict) -> None:
    session = None
    try:
        session = get_session()
        notif = Notification(
            event_type=event,
            payload=payload,
            # Use the event's real owner (Trade.user_id, threaded through
            # by execution/trade_engine.py + execution/paper_executor.py)
            # when present, so services/notification_service.py's
            # _owned_by() actually shows this notification to the user it
            # belongs to instead of only ever being visible to
            # _PRIMARY_USER_ID. Events with no owner concept (system
            # health, etc.) keep the existing single-tenant fallback.
            user_id=payload.get("user_id") or _PRIMARY_USER_ID,
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
            self._broadcast(message, payload.get("user_id"))

        # Trigger proactive Telegram alert if configured
        proactive_events = (
            TradeEvent.TRADE_OPENED,
            TradeEvent.TRADE_CLOSED,
            TradeEvent.SYSTEM_HEALTH_DEGRADED,
            TradeEvent.SYSTEM_HEALTH_RECOVERED,
        )
        if (
            event in proactive_events
            and self.telegram_bot_manager is not None
            and _telegram_alert_enabled(event)
        ):
            try:
                msg = ""
                if event == TradeEvent.TRADE_OPENED:
                    # Own send path (not the shared send_alert_threadsafe(msg)
                    # below) -- this one also carries a chart screenshot, sent
                    # as a photo+caption instead of a plain text message.
                    caption = _build_trade_opened_caption(payload)
                    self.telegram_bot_manager.send_trade_opened_alert_threadsafe(
                        caption, _trade_opened_chart_kwargs(payload)
                    )
                    return {"event": event, "payload": payload}
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

    def _broadcast(self, message: str, owner_user_id: int | None = None) -> None:
        # emit() (and therefore this) can run inside a worker thread with no
        # running loop of its own -- asyncio.get_running_loop() would raise
        # there, which the old code silently swallowed, dropping the
        # broadcast entirely. run_coroutine_threadsafe() against the loop
        # captured at construction time works from any thread.
        if self._loop is None:
            return
        # broadcast_to_owner() falls back to a full broadcast when
        # owner_user_id is None (system/health events, or a payload with no
        # user_id key) -- same behavior as the old unconditional broadcast().
        asyncio.run_coroutine_threadsafe(
            self.websocket_manager.broadcast_to_owner(message, owner_user_id), self._loop
        )
