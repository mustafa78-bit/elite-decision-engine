"""Captures a real screenshot of the app's own chart for the TRADE_OPENED
Telegram alert -- not a redrawn approximation. Headless-browses a bare
embed page (frontend/src/pages/ChartEmbed.tsx) that renders the exact same
ChartPanel component + overlays (S/R, RSI divergence, trend channel,
liquidity zones, volume profile) a user sees in the app, and crops the
screenshot to just that chart element.
"""

from __future__ import annotations

import logging
import urllib.parse

from auth.jwt import create_access_token
from config import TELEGRAM_CHART_EMBED_BASE_URL

logger = logging.getLogger(__name__)

# Matches notifications/dispatcher.py's single-tenant Telegram assumption --
# there's no per-user Telegram routing anywhere in this app yet, so the
# embed page is always screenshotted as this one account.
_PRIMARY_USER_ID = 1

# How long to wait for ChartPanel's onReady (all overlay fetches settled)
# before giving up and screenshotting whatever rendered so far -- a slow
# overlay fetch (e.g. a rate-limited exchange call) must not block the
# whole TRADE_OPENED alert indefinitely.
_READY_TIMEOUT_MS = 12_000
_NAV_TIMEOUT_MS = 15_000


# Fewer candles than the app's own default (200) so each one gets more
# horizontal room in the fixed 1280px-wide crop -- a "zoomed in" view reads
# far better at Telegram's thumbnail size than the same candles squeezed
# thin across the full history the in-app chart shows.
_EMBED_CANDLE_LIMIT = 60


def _build_embed_url(
    symbol: str,
    timeframe: str,
    side: str,
    entry: float | None,
    stop: float | None,
    tp1: float | None,
    tp2: float | None,
) -> str:
    token = create_access_token({"sub": str(_PRIMARY_USER_ID), "username": "telegram-bot"})
    params = {
        "symbol": symbol, "timeframe": timeframe, "side": side, "token": token,
        "limit": str(_EMBED_CANDLE_LIMIT),
    }
    if entry:
        params["entry"] = str(entry)
    if stop:
        params["stop"] = str(stop)
    if tp1:
        params["tp1"] = str(tp1)
    if tp2:
        params["tp2"] = str(tp2)
    query = urllib.parse.urlencode(params)
    return f"{TELEGRAM_CHART_EMBED_BASE_URL}/embed/chart?{query}"


async def capture_trade_chart_png(
    symbol: str,
    timeframe: str,
    side: str,
    entry: float | None,
    stop: float | None,
    tp1: float | None,
    tp2: float | None,
) -> bytes | None:
    """Screenshot the real chart for a just-opened trade as a PNG.

    Returns None (never raises) on any failure -- callers must fall back to
    a text-only alert rather than losing the whole TRADE_OPENED
    notification over a screenshot problem (headless browser unavailable,
    frontend not running, a slow/failed overlay fetch, etc).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("playwright not installed; skipping trade chart screenshot")
        return None

    url = _build_embed_url(symbol, timeframe, side, entry, stop, tp1, tp2)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                # device_scale_factor=2 renders at 2x pixel density (like a
                # retina screenshot) -- Telegram compresses images for its
                # chat thumbnails, and the symbol name/axis labels/timeframe
                # text were reported as too small/blurry to read at 1x.
                page = await browser.new_page(viewport={"width": 1280, "height": 550}, device_scale_factor=2)
                await page.goto(url, timeout=_NAV_TIMEOUT_MS, wait_until="domcontentloaded")
                try:
                    await page.wait_for_function(
                        "window.__CHART_READY__ === true", timeout=_READY_TIMEOUT_MS
                    )
                except Exception:
                    logger.warning(
                        "Chart embed for %s did not signal ready within %dms; "
                        "screenshotting whatever rendered so far",
                        symbol, _READY_TIMEOUT_MS,
                    )
                element = page.locator('[data-testid="chart-embed-root"]')
                return await element.screenshot(type="png")
            finally:
                await browser.close()
    except Exception as e:
        logger.warning("Failed to capture trade chart screenshot for %s: %s", symbol, e)
        return None
