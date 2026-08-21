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
    manager = TelegramBotManager(token="")
    setup_ok = manager.setup()
    assert setup_ok is False
    assert manager.application is None


class TestSendAlertRetriesOnFloodControl:
    """SPRINT_JULES_TELEGRAM_ALERT_FLOOD_NO_RATE_LIMITING.md.

    A burst of TRADE_CLOSED events (e.g. a mass stop-loss hit) fires one
    independent send per event with no spacing -- Telegram's real 429
    response surfaces as python-telegram-bot's RetryAfter. Previously
    send_alert()'s bare `except Exception` swallowed it silently on the
    first failure; now it retries after the server-specified delay.
    """

    def _manager_with_mock_bot(self):
        manager = TelegramBotManager(token="fake-token", chat_id="12345")
        manager.application = MagicMock()
        manager.application.bot.send_message = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_retries_and_succeeds_after_a_single_rate_limit_hit(self):
        from telegram.error import RetryAfter

        manager = self._manager_with_mock_bot()
        manager.application.bot.send_message.side_effect = [
            RetryAfter(retry_after=1),
            None,
        ]

        with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
            await manager.send_alert("Burst alert")

        assert manager.application.bot.send_message.call_count == 2
        mock_sleep.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries_without_raising(self):
        from telegram.error import RetryAfter

        manager = self._manager_with_mock_bot()
        manager.application.bot.send_message.side_effect = RetryAfter(retry_after=1)

        with patch("asyncio.sleep", new=AsyncMock()):
            # send_alert()'s own outer try/except keeps this from propagating,
            # matching the existing "never crash the caller" contract.
            await manager.send_alert("Burst alert")

        assert manager.application.bot.send_message.call_count == 4  # 1 + 3 retries

    @pytest.mark.asyncio
    async def test_no_retry_needed_when_send_succeeds_immediately(self):
        manager = self._manager_with_mock_bot()

        with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
            await manager.send_alert("Normal alert")

        assert manager.application.bot.send_message.call_count == 1
        mock_sleep.assert_not_awaited()


class TestSendPhoto:
    def _manager_with_mock_bot(self):
        manager = TelegramBotManager(token="fake-token", chat_id="12345")
        manager.application = MagicMock()
        manager.application.bot.send_photo = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_sends_photo_with_caption(self):
        manager = self._manager_with_mock_bot()

        await manager.send_photo(b"fake-png-bytes", "Caption text")

        manager.application.bot.send_photo.assert_awaited_once_with(
            chat_id="12345", photo=b"fake-png-bytes", caption="Caption text", parse_mode="HTML"
        )

    @pytest.mark.asyncio
    async def test_truncates_captions_over_1024_chars(self):
        manager = self._manager_with_mock_bot()
        long_caption = "x" * 2000

        await manager.send_photo(b"fake-png-bytes", long_caption)

        sent_caption = manager.application.bot.send_photo.call_args.kwargs["caption"]
        assert len(sent_caption) == 1024
        assert sent_caption.endswith("...")

    @pytest.mark.asyncio
    async def test_retries_on_flood_control(self):
        from telegram.error import RetryAfter

        manager = self._manager_with_mock_bot()
        manager.application.bot.send_photo.side_effect = [RetryAfter(retry_after=1), None]

        with patch("asyncio.sleep", new=AsyncMock()):
            await manager.send_photo(b"fake-png-bytes", "Caption")

        assert manager.application.bot.send_photo.call_count == 2

    @pytest.mark.asyncio
    async def test_no_op_when_not_configured(self):
        manager = TelegramBotManager(token="", chat_id="")
        # No .application set -- must not raise
        await manager.send_photo(b"fake-png-bytes", "Caption")


class TestSendTradeOpenedAlert:
    """SPRINT_JULES_MEGA_CHART_ANALYSIS_OVERLAYS.md-adjacent: TRADE_OPENED
    alerts now carry a real screenshot of the app's own chart (via
    services.telegram.chart_screenshot.capture_trade_chart_png), falling
    back to a text-only alert when the screenshot can't be captured."""

    def _manager_with_mock_bot(self):
        manager = TelegramBotManager(token="fake-token", chat_id="12345")
        manager.application = MagicMock()
        manager.application.bot.send_photo = AsyncMock()
        manager.application.bot.send_message = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_sends_photo_when_screenshot_succeeds(self):
        manager = self._manager_with_mock_bot()

        with patch(
            "services.telegram.chart_screenshot.capture_trade_chart_png",
            new=AsyncMock(return_value=b"fake-png-bytes"),
        ):
            await manager.send_trade_opened_alert("Caption", {"symbol": "BTCUSDT"})

        manager.application.bot.send_photo.assert_awaited_once()
        manager.application.bot.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_falls_back_to_text_alert_when_screenshot_fails(self):
        manager = self._manager_with_mock_bot()

        with patch(
            "services.telegram.chart_screenshot.capture_trade_chart_png",
            new=AsyncMock(return_value=None),
        ):
            await manager.send_trade_opened_alert("Caption", {"symbol": "BTCUSDT"})

        manager.application.bot.send_photo.assert_not_awaited()
        manager.application.bot.send_message.assert_awaited_once()

    def test_threadsafe_no_op_when_not_configured(self):
        manager = TelegramBotManager(token="", chat_id="")
        # No .application/.loop set -- must not raise
        manager.send_trade_opened_alert_threadsafe("Caption", {"symbol": "BTCUSDT"})
