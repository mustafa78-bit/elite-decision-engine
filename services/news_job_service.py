"""Periodic job: proactive Telegram alerts for market-moving crypto news and
institutional/VC project-funding news.

SPRINT_JULES_TELEGRAM_NEWS_ALERTS.md (originally written for Jules, later
implemented directly after Jules failed to push a branch).

Design notes:
  - RSS is fetched once per cycle (NewsService.fetch_rss_feeds()) and reused
    across all 25 FIXED_COIN_UNIVERSE symbols -- not refetched per symbol.
  - Sentiment is classified once per *unique* headline for the whole cycle,
    not once per (symbol, headline) pair, to avoid a per-symbol LLM-call
    multiplier on top of NVIDIA's already-observed rate limiting.
  - VC-funding detection is pure keyword matching (no LLM call at all).
  - Dedup via database.SentAlert -- a headline that already fired an alert
    in a previous cycle (even after a restart) never re-fires.
  - Deliberately bypasses NotificationDispatcher.emit(): these aren't
    trade/portfolio events the in-app notification center needs to persist,
    just two dedicated Telegram pushes.
"""

from __future__ import annotations

import logging

import database
from config import FIXED_COIN_UNIVERSE
from database import is_alert_sent, record_sent_alert
from market.intelligence.news import NewsService, headline_hash
from services.telegram.bot import TelegramBotManager

logger = logging.getLogger(__name__)

NEWS_JOB_INTERVAL_SECONDS = 1800  # 30 minutes

_PRIMARY_USER_ID = 1  # matches notifications/dispatcher.py's single-tenant Telegram assumption


def _bare_universe_symbols() -> list[str]:
    return [s.replace("USDT", "") for s in FIXED_COIN_UNIVERSE]


def _preference_enabled(key: str) -> bool:
    session = None
    try:
        session = database.get_session()
        settings = (
            session.query(database.UserSettings)
            .filter(database.UserSettings.user_id == _PRIMARY_USER_ID)
            .first()
        )
    except Exception as e:
        logger.warning("News job: failed to load notification preferences, defaulting to enabled: %s", e)
        return True
    finally:
        if session is not None:
            session.close()
    if settings is None or not settings.notification_preferences:
        return True
    return settings.notification_preferences.get(key, True)


def run_news_alert_cycle(news_service: NewsService | None = None) -> None:
    """Run one full poll cycle. Safe to call directly in tests (sync, no I/O
    beyond what NewsService/TelegramBotManager already isolate)."""
    ns = news_service or NewsService()

    try:
        entries = ns.fetch_rss_feeds()
    except Exception:
        logger.exception("News job: failed to fetch RSS feeds")
        return

    seen_titles: set[str] = set()
    unique_headlines: list[str] = []
    for entry in entries:
        title = (entry.get("title") or "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        unique_headlines.append(title)

    if not unique_headlines:
        return

    symbols = _bare_universe_symbols()
    matches_by_headline = {h: ns.match_headline_to_symbols(h, symbols) for h in unique_headlines}
    market_moving_candidates = [h for h, syms in matches_by_headline.items() if syms]

    # One batched sentiment call for the whole cycle's unique, symbol-matching
    # headlines -- not one call per symbol.
    sentiment_by_headline = ns.classify_sentiment(market_moving_candidates) if market_moving_candidates else {}

    vc_enabled = _preference_enabled("vc_funding_news")
    news_enabled = _preference_enabled("market_news")
    news_bot = TelegramBotManager.get_instance("news")
    vc_bot = TelegramBotManager.get_instance("vc_funding")

    for headline in unique_headlines:
        h_hash = headline_hash(headline)

        vc_institutions = ns.detect_vc_funding(headline)
        if vc_institutions:
            if vc_enabled and not is_alert_sent("vc_funding_news", h_hash):
                names = ", ".join(i.title() for i in vc_institutions)
                msg = f"🏛️ <b>VC FUNDING NEWS</b>\n{headline}\nBackers: {names}"
                vc_bot.send_alert_threadsafe(msg)
                record_sent_alert("vc_funding_news", h_hash)
            # A funding headline is tagged as VC news, not also re-sent
            # through the market-moving path below.
            continue

        matched_symbols = matches_by_headline.get(headline, [])
        if not matched_symbols:
            continue

        sentiment = sentiment_by_headline.get(headline.strip().lower(), "neutral")
        if sentiment == "neutral":
            continue

        if not news_enabled or is_alert_sent("market_news", h_hash):
            continue

        emoji = "🟢" if sentiment == "positive" else "🔴"
        msg = f"{emoji} <b>{sentiment.upper()} NEWS</b>\n{headline}\nSymbols: {', '.join(matched_symbols)}"
        news_bot.send_alert_threadsafe(msg)
        record_sent_alert("market_news", h_hash)
