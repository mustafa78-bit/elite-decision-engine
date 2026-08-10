from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import Application, CommandHandler, ContextTypes

from config import (
    TELEGRAM_ALLOWED_CHAT_IDS,
    TELEGRAM_CHAT_ID,
    TELEGRAM_NEWS_CHAT_ID,
    TELEGRAM_NEWS_TOKEN,
    TELEGRAM_TOKEN,
    TELEGRAM_VC_CHAT_ID,
    TELEGRAM_VC_TOKEN,
)
from monitoring.health import HealthService

logger = logging.getLogger(__name__)


def chunk_text(text: str) -> list[str]:
    """Splits a message into chunks of at most 4096 characters to prevent failures."""
    max_length = 4096
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""
    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line
    if current_chunk:
        chunks.append(current_chunk)

    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_length:
            # Fallback character-based split for abnormally long lines
            for i in range(0, len(chunk), max_length):
                final_chunks.append(chunk[i:i + max_length])
        else:
            final_chunks.append(chunk)
    return final_chunks

# Parse TELEGRAM_ALLOWED_CHAT_IDS into a set of integers or strings
allowed_ids: set[Any] = set()
if TELEGRAM_ALLOWED_CHAT_IDS:
    for item in TELEGRAM_ALLOWED_CHAT_IDS.split(","):
        item = item.strip()
        if item:
            try:
                allowed_ids.add(int(item))
            except ValueError:
                allowed_ids.add(item)


def authorized_only(func):
    """Decorator to enforce TELEGRAM_ALLOWED_CHAT_IDS security."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update or not update.effective_chat:
            return
        chat_id = update.effective_chat.id
        # Only enforce if allowed_ids has been configured
        if allowed_ids and chat_id not in allowed_ids and str(chat_id) not in allowed_ids:
            logger.warning("Unauthorized command execution attempt from chat_id: %s", chat_id)
            await update.message.reply_text("You're not authorized to use this bot.")
            return
        return await func(update, context)
    return wrapper


async def send_long_message(update: Update, text: str):
    """Automatically splits and sends messages longer than 4096 characters to prevent failures."""
    chunks = chunk_text(text)
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="HTML")


_ollo_service: Any | None = None


def get_ollo_service() -> Any:
    """Helper to initialize OLLOService on demand."""
    global _ollo_service
    if _ollo_service is None:
        from services.ai.provider_factory import create_ai_service
        from services.ollo.ollo_service import OLLOService
        ai_svc = create_ai_service()
        _ollo_service = OLLOService(ai_svc)
    return _ollo_service


@authorized_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and format scannable operational status."""
    logger.info("Handling Telegram /status command from chat_id=%s", update.effective_chat.id)
    try:
        # Run potentially blocking checks in thread pool
        health = await asyncio.to_thread(HealthService.full)
        overall = health.get("status", "unknown")

        offline_subsystems = []

        # Check Database
        db_status = health.get("database", {})
        if db_status.get("status") != "ok":
            offline_subsystems.append(f"• <b>Database</b>: offline/error ({db_status.get('detail', 'unknown error')})")

        # Check Collector
        col_status = health.get("collector", {})
        if col_status.get("status") != "ok":
            offline_subsystems.append(f"• <b>Market Data Collector</b>: offline/error ({col_status.get('detail', 'unknown error')})")

        # Check Execution Engine
        exec_status = health.get("execution", {})
        if exec_status.get("status") == "error" or not exec_status.get("pipeline_ready", True):
            offline_subsystems.append(f"• <b>Execution Engine</b>: degraded/offline ({exec_status.get('detail', 'unknown')})")

        # Check Dependencies
        deps = health.get("dependencies", {})
        for dep_name, dep_info in deps.items():
            if dep_info.get("status") != "ok":
                offline_subsystems.append(f"• <b>Dependency ({dep_name})</b>: offline ({dep_info.get('detail', 'unknown')})")

        if overall == "ok" and not offline_subsystems:
            message = "🟢 <b>NEXUS</b> — all systems operational"
        else:
            message = "⚠️ <b>NEXUS</b> — systems degraded\n\n" + "\n".join(offline_subsystems)

        await update.message.reply_text(message, parse_mode="HTML")
    except Exception as e:
        logger.exception("Error during /status generation")
        await update.message.reply_text(f"❌ Error fetching status: {str(e)}")


@authorized_only
async def brief_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers the morning Ollo briefing generation and sends it with a bold title."""
    logger.info("Handling Telegram /brief command from chat_id=%s", update.effective_chat.id)
    processing_msg = await update.message.reply_text("⚡ Generating morning briefing, please wait...")
    try:
        ollo = get_ollo_service()
        briefing = await asyncio.to_thread(ollo.briefing, "morning", "command_deck")

        message = f"<b>{briefing.title}</b>\n\n{briefing.text}"

        try:
            await processing_msg.delete()
        except Exception:
            pass

        await send_long_message(update, message)
    except Exception as e:
        logger.exception("Error during /brief generation")
        try:
            await processing_msg.edit_text(f"❌ Error generating briefing: {str(e)}")
        except Exception:
            await update.message.reply_text(f"❌ Error generating briefing: {str(e)}")


@authorized_only
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes free-form questions through OLLOService.query()."""
    logger.info("Handling Telegram /ask command from chat_id=%s", update.effective_chat.id)
    message_text = update.message.text or ""
    query = ""
    if message_text.startswith("/ask"):
        query = message_text[4:].strip()

    if not query:
        await update.message.reply_text("Please provide a question. Usage: /ask &lt;your question&gt;", parse_mode="HTML")
        return

    processing_msg = await update.message.reply_text("💭 Consulting OLLO, please wait...")
    try:
        ollo = get_ollo_service()
        response = await asyncio.to_thread(ollo.query, query, "command_deck")

        message = response.text

        intent_route = getattr(response, "intent_route", None)
        if intent_route:
            route_name = intent_route.lstrip("/")
            message += f"\n\n<i>(This relates to your {route_name})</i>"

        try:
            await processing_msg.delete()
        except Exception:
            pass

        await send_long_message(update, message)
    except Exception as e:
        logger.exception("Error during /ask generation")
        try:
            await processing_msg.edit_text(f"❌ Error consulting OLLO: {str(e)}")
        except Exception:
            await update.message.reply_text(f"❌ Error consulting OLLO: {str(e)}")


# Credentials per named bot instance. "trades" is the original bot (status/
# brief/ask commands, trade + system-health alerts) -- its env vars are
# unchanged from before multi-bot support existed. "news" and "vc_funding"
# are separate, push-only bots (own token/chat, no commands) added for
# proactive market-news / institutional-funding alerts.
_INSTANCE_CREDENTIALS: dict[str, tuple[str, str]] = {
    "trades": (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID),
    "news": (TELEGRAM_NEWS_TOKEN, TELEGRAM_NEWS_CHAT_ID),
    "vc_funding": (TELEGRAM_VC_TOKEN, TELEGRAM_VC_CHAT_ID),
}


class TelegramBotManager:
    _instances: dict[str, TelegramBotManager] = {}

    def __init__(self, name: str = "trades", token: str = "", chat_id: str = ""):
        self.name = name
        self.token = token
        self.chat_id = chat_id
        self.application: Application | None = None
        self.loop: asyncio.AbstractEventLoop | None = None

    @classmethod
    def get_instance(cls, name: str = "trades") -> TelegramBotManager:
        if name not in cls._instances:
            token, chat_id = _INSTANCE_CREDENTIALS.get(name, ("", ""))
            cls._instances[name] = cls(name=name, token=token, chat_id=chat_id)
        return cls._instances[name]

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Sets the reference to the main thread's event loop."""
        self.loop = loop
        logger.info("TelegramBotManager('%s') main event loop set successfully.", self.name)

    async def send_alert(self, text: str) -> None:
        """Coroutine to send a proactive message directly to this instance's chat."""
        if not self.application:
            logger.debug("Telegram alert skipped: bot '%s' not setup", self.name)
            return

        if not self.token or not self.chat_id:
            logger.debug("Telegram alert skipped: '%s' token or chat ID not configured", self.name)
            return

        try:
            chunks = chunk_text(text)
            for chunk in chunks:
                await self._send_message_with_retry(chunk)
            logger.info("Telegram proactive alert sent successfully via '%s'.", self.name)
        except Exception as e:
            logger.warning("Failed to send Telegram alert via '%s': %s", self.name, e)

    async def _send_message_with_retry(self, chunk: str, max_retries: int = 3) -> None:
        """Send one chunk, retrying on Telegram's own flood-control signal.

        A burst of TRADE_CLOSED events (e.g. every open position hitting its
        stop-loss in the same tick) fires one independent send per event with
        no spacing between them -- python-telegram-bot raises RetryAfter
        (Telegram's real 429 response) when that burst exceeds ~1 msg/sec per
        chat. Retrying after the server-specified delay recovers messages
        that would otherwise be silently dropped by send_alert()'s bare
        `except Exception`; it doesn't prevent the burst itself (that's
        option (b), a larger digest/coalescing redesign, scoped separately).
        """
        for attempt in range(max_retries + 1):
            try:
                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=chunk,
                    parse_mode="HTML"
                )
                return
            except RetryAfter as e:
                if attempt >= max_retries:
                    raise
                wait_seconds = e.retry_after.total_seconds() if hasattr(e.retry_after, "total_seconds") else float(e.retry_after)
                logger.warning(
                    "Telegram flood control hit on '%s', retrying in %.1fs (attempt %d/%d)",
                    self.name, wait_seconds, attempt + 1, max_retries,
                )
                await asyncio.sleep(wait_seconds)

    def send_alert_threadsafe(self, text: str) -> None:
        """Thread-safe method to trigger the send_alert coroutine on the captured main loop."""
        if not self.application or not self.token or not self.chat_id:
            logger.debug("Telegram alert skipped: '%s' bot or credentials not configured", self.name)
            return

        if not self.loop:
            logger.warning("Telegram alert skipped: '%s' main event loop reference is missing", self.name)
            return

        # Schedule the send_alert coroutine on the captured main loop thread-safely
        coro = self.send_alert(text)
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def setup(self) -> bool:
        if not self.token:
            logger.warning("Telegram bot '%s': token not set, will not be initialized.", self.name)
            return False

        try:
            self.application = Application.builder().token(self.token).build()

            # /status, /brief, /ask are specific to the original trades/health
            # bot -- the news/vc_funding bots are push-only broadcast
            # destinations with no interactive commands.
            if self.name == "trades":
                self.application.add_handler(CommandHandler("status", status_command))
                self.application.add_handler(CommandHandler("brief", brief_command))
                self.application.add_handler(CommandHandler("ask", ask_command))

            logger.info("Telegram bot '%s' setup completed successfully.", self.name)
            return True
        except Exception as e:
            logger.error("Failed to setup Telegram bot '%s': %s", self.name, e)
            return False

    async def start(self) -> None:
        if not self.application:
            return
        try:
            await self.application.initialize()
            if self.name == "trades":
                await self.application.start()
                await self.application.updater.start_polling()
                logger.info("Telegram bot '%s' started polling successfully.", self.name)
            else:
                logger.info("Telegram bot '%s' initialized (push-only, no polling).", self.name)
        except Exception as e:
            logger.error("Failed to start Telegram bot '%s': %s", self.name, e)

    async def stop(self) -> None:
        if not self.application:
            return
        try:
            if self.name == "trades":
                await self.application.updater.stop()
                await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot '%s' stopped successfully.", self.name)
        except Exception as e:
            logger.error("Failed to stop Telegram bot '%s': %s", self.name, e)
