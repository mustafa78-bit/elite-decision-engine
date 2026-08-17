"""Periodic job: proactive Telegram alerts for market-moving crypto news,
US Fed/macro news, and institutional/VC project-funding news.

SPRINT_JULES_TELEGRAM_NEWS_ALERTS.md (originally written for Jules, later
implemented directly after Jules failed to push a branch).
SPRINT_JULES_NEWS_BOT_V2_SCORE_TRANSLATE_MACRO.md (v2: impact score, Turkish
translation, US macro/Fed coverage -- also implemented directly).

Design notes:
  - RSS is fetched once per cycle (NewsService.fetch_rss_feeds() +
    fetch_macro_rss_feeds()) and reused across all 25 FIXED_COIN_UNIVERSE
    symbols -- not refetched per symbol.
  - Sentiment+score are classified once per *unique* headline for the whole
    cycle (crypto and macro headlines batched into the SAME call), not once
    per (symbol, headline) pair, to avoid a per-symbol LLM-call multiplier
    on top of NVIDIA's already-observed rate limiting.
  - Translation is a separate, non-NVIDIA step (NewsService.translate_to_turkish())
    -- deliberately not batched into the sentiment/score call, and only run
    for headlines that actually pass the filters below and are about to be
    sent, not for every fetched headline.
  - VC-funding detection is pure keyword matching (no LLM call at all) --
    unchanged from v1, stays in English.
  - Macro headlines (US Fed/economic news with no coin ticker) are tagged as
    broadly relevant to BTC, the market-wide proxy this codebase already
    uses elsewhere (see market/context/'s BTC-health-as-market-regime
    pattern), rather than requiring a symbol match.
  - Dedup via database.SentAlert -- a headline that already fired an alert
    in a previous cycle (even after a restart) never re-fires.
  - Deliberately bypasses NotificationDispatcher.emit(): these aren't
    trade/portfolio events the in-app notification center needs to persist,
    just two dedicated Telegram pushes.
"""

from __future__ import annotations

import logging

import database
from config import FIXED_COIN_UNIVERSE, NEWS_MIN_IMPACT_SCORE
from database import is_alert_sent, record_sent_alert
from market.intelligence.news import NewsService, headline_hash
from services.telegram.bot import TelegramBotManager

logger = logging.getLogger(__name__)

NEWS_JOB_INTERVAL_SECONDS = 1800  # 30 minutes

_PRIMARY_USER_ID = 1  # matches notifications/dispatcher.py's single-tenant Telegram assumption

_SENTIMENT_TR = {"positive": "POZİTİF", "negative": "NEGATİF"}


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


def _dedupe_titles(entries: list[dict[str, str]], seen_titles: set[str]) -> list[str]:
    unique: list[str] = []
    for entry in entries:
        title = (entry.get("title") or "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        unique.append(title)
    return unique


def run_news_alert_cycle(news_service: NewsService | None = None) -> None:
    """Run one full poll cycle. Safe to call directly in tests (sync, no I/O
    beyond what NewsService/TelegramBotManager already isolate)."""
    ns = news_service or NewsService()

    try:
        crypto_entries = ns.fetch_rss_feeds()
    except Exception:
        logger.exception("News job: failed to fetch RSS feeds")
        crypto_entries = []

    try:
        macro_entries = ns.fetch_macro_rss_feeds()
    except Exception:
        logger.exception("News job: failed to fetch macro RSS feeds")
        macro_entries = []

    seen_titles: set[str] = set()
    unique_crypto_headlines = _dedupe_titles(crypto_entries, seen_titles)
    unique_macro_headlines = [h for h in _dedupe_titles(macro_entries, seen_titles) if ns.is_macro_headline(h)]

    if not unique_crypto_headlines and not unique_macro_headlines:
        return

    symbols = _bare_universe_symbols()
    matches_by_headline = {h: ns.match_headline_to_symbols(h, symbols) for h in unique_crypto_headlines}
    market_moving_candidates = [h for h, syms in matches_by_headline.items() if syms]

    # One batched sentiment+score call for the whole cycle's unique
    # candidates -- crypto AND macro headlines together, not one call per
    # symbol and not a separate call for macro.
    scoring_candidates = market_moving_candidates + unique_macro_headlines
    scored_by_headline = ns.classify_and_score(scoring_candidates) if scoring_candidates else {}

    vc_enabled = _preference_enabled("vc_funding_news")
    news_enabled = _preference_enabled("market_news")
    news_bot = TelegramBotManager.get_instance("news")
    vc_bot = TelegramBotManager.get_instance("vc_funding")

    def _send_market_alert(headline: str, symbols_label: str) -> None:
        h_hash = headline_hash(headline)
        if not news_enabled or is_alert_sent("market_news", h_hash):
            return

        scored = scored_by_headline.get(headline.strip().lower())
        if scored is None:
            return
        sentiment = scored["sentiment"]
        if sentiment == "neutral":
            return
        # The score was always computed and shown in the alert text but
        # never actually gated whether one fired -- a routine, barely-
        # relevant headline sent exactly as readily as genuinely
        # market-moving news. Deliberately does NOT call record_sent_alert()
        # for a below-threshold headline: it was never actually pushed, so
        # marking it "sent" would be dishonest bookkeeping. If the same
        # headline is still in the feed next cycle it's simply re-scored
        # (cheap -- still one batched call either way, not a per-headline
        # one) rather than permanently write-marked as delivered.
        if scored["score"] < NEWS_MIN_IMPACT_SCORE:
            return

        headline_tr = ns.translate_to_turkish(headline)
        emoji = "🟢" if sentiment == "positive" else "🔴"
        sentiment_tr = _SENTIMENT_TR.get(sentiment, sentiment.upper())
        msg = (
            f"{emoji} <b>{sentiment_tr} HABER (Etki: {scored['score']}/100)</b>\n"
            f"{headline_tr}\n"
            f"Semboller: {symbols_label}"
        )
        news_bot.send_alert_threadsafe(msg)
        record_sent_alert("market_news", h_hash)

    for headline in unique_crypto_headlines:
        vc_institutions = ns.detect_vc_funding(headline)
        if vc_institutions:
            h_hash = headline_hash(headline)
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

        _send_market_alert(headline, ", ".join(matched_symbols))

    for headline in unique_macro_headlines:
        # BTC as the market-wide proxy -- no coin ticker to match against for
        # a pure macro headline, matching how this codebase already treats
        # BTC as the general market-regime indicator elsewhere.
        _send_market_alert(headline, "BTC (Genel Piyasa)")
