from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from services.telegram.bot import (
    TelegramBotManager,
    allowed_ids,
    ask_command,
    authorized_only,
    brief_command,
    send_long_message,
    status_command,
)


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update."""
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    chat = MagicMock(spec=Chat)
    user = MagicMock(spec=User)

    chat.id = 12345
    user.id = 12345
    message.chat_id = 12345
    message.text = "/status"
    message.reply_text = AsyncMock()
    message.delete = AsyncMock()

    update.effective_chat = chat
    update.effective_user = user
    update.message = message
    return update


@pytest.fixture
def mock_context():
    """Create a mock telegram Context."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_authorized_only_decorator_allowed(mock_update, mock_context):
    # Set allowed IDs
    allowed_ids.clear()
    allowed_ids.add(12345)

    called = False

    @authorized_only
    async def sample_handler(update, context):
        nonlocal called
        called = True

    await sample_handler(mock_update, mock_context)
    assert called is True
    mock_update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_authorized_only_decorator_denied(mock_update, mock_context):
    # Set allowed IDs (user id is 12345, so 99999 is unauthorized)
    allowed_ids.clear()
    allowed_ids.add(99999)

    called = False

    @authorized_only
    async def sample_handler(update, context):
        nonlocal called
        called = True

    await sample_handler(mock_update, mock_context)
    assert called is False
    mock_update.message.reply_text.assert_called_once_with("You're not authorized to use this bot.")


@pytest.mark.asyncio
async def test_send_long_message_short(mock_update):
    text = "Short message"
    await send_long_message(mock_update, text)
    mock_update.message.reply_text.assert_called_once_with("Short message", parse_mode="HTML")


@pytest.mark.asyncio
async def test_send_long_message_long(mock_update):
    # Generate line-based string exceeding 4096 chars
    lines = ["Line " + str(i) for i in range(1000)]
    long_text = "\n".join(lines)
    assert len(long_text) > 4096

    await send_long_message(mock_update, long_text)
    # Ensure reply_text was called multiple times
    assert mock_update.message.reply_text.call_count > 1


@pytest.mark.asyncio
async def test_status_command_operational(mock_update, mock_context):
    allowed_ids.clear() # Allow all if empty in test context, or add user id
    allowed_ids.add(12345)

    mock_health = {
        "status": "ok",
        "database": {"status": "ok"},
        "collector": {"status": "ok"},
        "execution": {"status": "ok", "pipeline_ready": True},
        "dependencies": {},
    }

    with patch("monitoring.health.HealthService.full", return_value=mock_health):
        await status_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    reply_text = mock_update.message.reply_text.call_args[0][0]
    assert "operational" in reply_text
    assert "NEXUS" in reply_text


@pytest.mark.asyncio
async def test_status_command_degraded(mock_update, mock_context):
    allowed_ids.clear()
    allowed_ids.add(12345)

    mock_health = {
        "status": "degraded",
        "database": {"status": "error", "detail": "Connection refused"},
        "collector": {"status": "ok"},
        "execution": {"status": "ok", "pipeline_ready": True},
        "dependencies": {"test_service": {"status": "error", "detail": "Timeout"}},
    }

    with patch("monitoring.health.HealthService.full", return_value=mock_health):
        await status_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    reply_text = mock_update.message.reply_text.call_args[0][0]
    assert "degraded" in reply_text
    assert "Database" in reply_text
    assert "Connection refused" in reply_text
    assert "test_service" in reply_text


@pytest.mark.asyncio
async def test_brief_command_success(mock_update, mock_context):
    allowed_ids.clear()
    allowed_ids.add(12345)

    mock_update.message.reply_text = AsyncMock(return_value=mock_update.message)

    # Mock OLLO response
    mock_briefing = MagicMock()
    mock_briefing.title = "Test Briefing Title"
    mock_briefing.text = "This is the briefing body contents."

    mock_ollo_svc = MagicMock()
    mock_ollo_svc.briefing.return_value = mock_briefing

    with patch("services.telegram.bot.get_ollo_service", return_value=mock_ollo_svc):
        await brief_command(mock_update, mock_context)

    # Verifies processing message is sent first, then briefing is sent
    assert mock_update.message.reply_text.call_count >= 2
    mock_update.message.delete.assert_called_once()

    # Verify formatting (bold title)
    briefing_sent = mock_update.message.reply_text.call_args_list[-1][0][0]
    assert "<b>Test Briefing Title</b>" in briefing_sent
    assert "This is the briefing body contents." in briefing_sent


@pytest.mark.asyncio
async def test_ask_command_no_query(mock_update, mock_context):
    allowed_ids.clear()
    allowed_ids.add(12345)

    mock_update.message.text = "/ask"
    await ask_command(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once_with(
        "Please provide a question. Usage: /ask &lt;your question&gt;", parse_mode="HTML"
    )


@pytest.mark.asyncio
async def test_ask_command_success_with_intent(mock_update, mock_context):
    allowed_ids.clear()
    allowed_ids.add(12345)

    mock_update.message.text = "/ask what is btc price?"
    mock_update.message.reply_text = AsyncMock(return_value=mock_update.message)

    mock_response = MagicMock()
    mock_response.text = "OLLO replies that BTC is bullish."
    mock_response.intent_route = "/portfolio"

    mock_ollo_svc = MagicMock()
    mock_ollo_svc.query.return_value = mock_response

    with patch("services.telegram.bot.get_ollo_service", return_value=mock_ollo_svc):
        await ask_command(mock_update, mock_context)

    assert mock_update.message.reply_text.call_count >= 2
    mock_update.message.delete.assert_called_once()

    # Verify intent route friendly mention is appended
    query_reply = mock_update.message.reply_text.call_args_list[-1][0][0]
    assert "OLLO replies that BTC is bullish." in query_reply
    assert "This relates to your portfolio" in query_reply


def test_telegram_bot_manager_no_token():
    with patch("services.telegram.bot.TELEGRAM_TOKEN", ""):
        manager = TelegramBotManager()
        setup_ok = manager.setup()
        assert setup_ok is False
        assert manager.application is None
