from __future__ import annotations

import asyncio
import logging
from typing import Optional, Set, Any

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import TELEGRAM_TOKEN, TELEGRAM_ALLOWED_CHAT_IDS
from monitoring.health import HealthService

logger = logging.getLogger(__name__)

# Parse TELEGRAM_ALLOWED_CHAT_IDS into a set of integers or strings
allowed_ids: Set[Any] = set()
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
    MAX_LENGTH = 4096
    if len(text) <= MAX_LENGTH:
        await update.message.reply_text(text, parse_mode="HTML")
        return

    chunks = []
    current_chunk = ""
    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > MAX_LENGTH:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line
    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        if len(chunk) > MAX_LENGTH:
            # Fallback character-based split for abnormally long lines
            for i in range(0, len(chunk), MAX_LENGTH):
                await update.message.reply_text(chunk[i:i + MAX_LENGTH], parse_mode="HTML")
        else:
            await update.message.reply_text(chunk, parse_mode="HTML")


_ollo_service: Optional[Any] = None


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


class TelegramBotManager:
    _instance: Optional[TelegramBotManager] = None

    def __init__(self):
        self.application: Optional[Application] = None

    @classmethod
    def get_instance(cls) -> TelegramBotManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def setup(self) -> bool:
        if not TELEGRAM_TOKEN:
            logger.warning("TELEGRAM_TOKEN not set. Telegram bot will not be initialized.")
            return False

        try:
            self.application = Application.builder().token(TELEGRAM_TOKEN).build()

            # Register handlers
            self.application.add_handler(CommandHandler("status", status_command))
            self.application.add_handler(CommandHandler("brief", brief_command))
            self.application.add_handler(CommandHandler("ask", ask_command))

            logger.info("Telegram bot setup completed successfully.")
            return True
        except Exception as e:
            logger.error("Failed to setup Telegram bot: %s", e)
            return False

    async def start(self) -> None:
        if not self.application:
            return
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot started polling successfully.")
        except Exception as e:
            logger.error("Failed to start Telegram bot polling: %s", e)

    async def stop(self) -> None:
        if not self.application:
            return
        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped successfully.")
        except Exception as e:
            logger.error("Failed to stop Telegram bot: %s", e)
