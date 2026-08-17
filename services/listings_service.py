"""Periodic job: proactive Telegram alerts for new Binance spot listings.

Design notes:
  - Binance only for now, not OKX/Bybit -- Binance has a real, stable JSON
    announcements API (verified live, 2026-08-17); OKX/Bybit don't expose an
    equivalent, and scraping their announcement pages would be far more
    fragile (breaks on any HTML/layout change). Revisit if this proves
    valuable enough to justify that extra fragility.
  - The "New Cryptocurrency Listing" catalog (catalogId=48) mixes several
    announcement subtypes under one ID -- futures perpetual contract
    launches, bStocks tokenized-security collateral/trading-pair additions
    -- none of which are a brand-new coin's first Binance *spot* listing.
    Confirmed live: Binance's own reliable signal for that is its "Will
    List <Coin> (<TICKER>)" title convention, used specifically for new
    listings, so that's what's filtered on rather than trusting the
    catalog's contents wholesale.
  - Dedup via database.SentAlert, same table market-news/VC alerts already
    use, keyed by the announcement's own numeric id (Binance already
    guarantees this is unique and stable) rather than a text hash.
  - Routes through the existing "vc_funding" Telegram bot (at the user's
    request), not a separate bot -- still its own notification-preference
    key ("new_listings"), so it can be toggled independently of VC-funding
    alerts even while sharing the same bot/chat.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests

from database import is_alert_sent, record_sent_alert
from services.telegram.bot import TelegramBotManager

logger = logging.getLogger(__name__)

LISTINGS_JOB_INTERVAL_SECONDS = 1800  # 30 minutes, matches news_job_service.py's cadence

_PRIMARY_USER_ID = 1  # matches notifications/dispatcher.py's single-tenant Telegram assumption

BINANCE_ANNOUNCEMENTS_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
BINANCE_NEW_LISTING_CATALOG_ID = 48

_WILL_LIST_PATTERN = re.compile(r"will list", re.IGNORECASE)
_TICKER_PATTERN = re.compile(r"([A-Za-z0-9][A-Za-z0-9.\- ]*?)\s*\(([A-Z0-9]{2,15})\)")


def _preference_enabled(key: str) -> bool:
    # Same pattern as news_job_service.py's _preference_enabled() /
    # notifications/dispatcher.py's _telegram_alert_enabled() -- this
    # codebase keeps one small private copy per alert source rather than a
    # shared helper, established convention, not duplicated by accident.
    import database

    session = None
    try:
        session = database.get_session()
        settings = (
            session.query(database.UserSettings)
            .filter(database.UserSettings.user_id == _PRIMARY_USER_ID)
            .first()
        )
    except Exception as e:
        logger.warning("Listings job: failed to load notification preferences, defaulting to enabled: %s", e)
        return True
    finally:
        if session is not None:
            session.close()
    if settings is None or not settings.notification_preferences:
        return True
    return settings.notification_preferences.get(key, True)


def fetch_binance_new_listings(limit: int = 20) -> list[dict[str, Any]]:
    """Fetch recent Binance announcements and filter down to genuine new
    spot listings -- see the module docstring for why catalogId=48 alone
    isn't a clean enough signal on its own.

    Returns a list of {"id": str, "title": str, "tickers": list[str]},
    newest first (matching the API's own ordering). Never raises -- a
    fetch failure logs a warning and returns an empty list, same
    resilience convention as market/intelligence/news.py's RSS fetchers.
    """
    try:
        response = requests.get(
            BINANCE_ANNOUNCEMENTS_URL,
            params={"type": 1, "pageNo": 1, "pageSize": limit, "catalogId": BINANCE_NEW_LISTING_CATALOG_ID},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.warning("Failed to fetch Binance new-listing announcements: %s", e)
        return []
    except ValueError as e:
        logger.warning("Failed to parse Binance new-listing announcements response: %s", e)
        return []

    catalogs = (data.get("data") or {}).get("catalogs") or []
    if not catalogs:
        return []
    articles = catalogs[0].get("articles") or []

    listings: list[dict[str, Any]] = []
    for article in articles:
        title = article.get("title") or ""
        article_id = article.get("id")
        if article_id is None or not _WILL_LIST_PATTERN.search(title):
            continue
        tickers = [m.group(2) for m in _TICKER_PATTERN.finditer(title)]
        if not tickers:
            continue
        listings.append({"id": str(article_id), "title": title, "tickers": tickers})
    return listings


def run_listings_alert_cycle(news_service: Any | None = None) -> None:
    """Run one full poll cycle. Safe to call directly in tests (sync, no
    I/O beyond what fetch_binance_new_listings/TelegramBotManager already
    isolate)."""
    if not _preference_enabled("new_listings"):
        return

    listings = fetch_binance_new_listings()
    if not listings:
        return

    from market.intelligence.news import NewsService
    ns = news_service or NewsService()

    bot = TelegramBotManager.get_instance("vc_funding")
    category = "new_listing"

    for listing in listings:
        if is_alert_sent(category, listing["id"]):
            continue

        title_tr = ns.translate_to_turkish(listing["title"])
        msg = (
            f"🆕 <b>YENİ LİSTELEME (Binance Spot)</b>\n"
            f"{title_tr}\n"
            f"Semboller: {', '.join(listing['tickers'])}"
        )
        bot.send_alert_threadsafe(msg)
        record_sent_alert(category, listing["id"])
