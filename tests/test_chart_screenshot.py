from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.telegram.chart_screenshot import _build_embed_url, capture_trade_chart_png


def test_build_embed_url_includes_a_real_signed_token():
    url = _build_embed_url("BTCUSDT", "1h", "LONG", entry=60000.0, stop=59000.0, tp1=61500.0, tp2=None)

    assert url.startswith("http")
    assert "/embed/chart?" in url
    assert "symbol=BTCUSDT" in url
    assert "timeframe=1h" in url
    assert "side=LONG" in url
    assert "entry=60000.0" in url
    assert "stop=59000.0" in url
    assert "tp1=61500.0" in url
    # tp2=None must be omitted, not serialized as the literal string "None"
    assert "tp2" not in url
    assert "token=" in url

    # The token itself must decode as a real access token for the primary
    # (single-tenant) user -- this is what lets the embed page's own
    # authenticated fetches (candles, overlays) succeed.
    from auth.jwt import decode_access_token
    token = url.split("token=")[1].split("&")[0]
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"


@pytest.mark.asyncio
async def test_capture_returns_none_when_playwright_not_installed():
    with patch.dict("sys.modules", {"playwright.async_api": None}):
        result = await capture_trade_chart_png("BTCUSDT", "1h", "LONG", 60000.0, 59000.0, 61500.0, None)
    assert result is None


@pytest.mark.asyncio
async def test_capture_returns_png_bytes_on_success():
    mock_element = MagicMock()
    mock_element.screenshot = AsyncMock(return_value=b"fake-png-bytes")

    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_function = AsyncMock()
    mock_page.locator = MagicMock(return_value=mock_element)

    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()

    mock_chromium = MagicMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright_instance = MagicMock()
    mock_playwright_instance.chromium = mock_chromium

    mock_playwright_cm = MagicMock()
    mock_playwright_cm.__aenter__ = AsyncMock(return_value=mock_playwright_instance)
    mock_playwright_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("playwright.async_api.async_playwright", return_value=mock_playwright_cm):
        result = await capture_trade_chart_png("BTCUSDT", "1h", "LONG", 60000.0, 59000.0, 61500.0, None)

    assert result == b"fake-png-bytes"
    mock_browser.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_capture_still_screenshots_when_ready_signal_times_out():
    # A slow/failed overlay fetch inside the embed page must not block the
    # whole alert forever -- screenshot whatever rendered instead.
    mock_element = MagicMock()
    mock_element.screenshot = AsyncMock(return_value=b"fake-png-bytes")

    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_function = AsyncMock(side_effect=TimeoutError("timed out"))
    mock_page.locator = MagicMock(return_value=mock_element)

    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()

    mock_chromium = MagicMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright_instance = MagicMock()
    mock_playwright_instance.chromium = mock_chromium

    mock_playwright_cm = MagicMock()
    mock_playwright_cm.__aenter__ = AsyncMock(return_value=mock_playwright_instance)
    mock_playwright_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("playwright.async_api.async_playwright", return_value=mock_playwright_cm):
        result = await capture_trade_chart_png("BTCUSDT", "1h", "LONG", 60000.0, 59000.0, 61500.0, None)

    assert result == b"fake-png-bytes"


@pytest.mark.asyncio
async def test_capture_returns_none_and_never_raises_on_browser_launch_failure():
    with patch("playwright.async_api.async_playwright", side_effect=RuntimeError("browser unavailable")):
        result = await capture_trade_chart_png("BTCUSDT", "1h", "LONG", 60000.0, 59000.0, 61500.0, None)
    assert result is None
