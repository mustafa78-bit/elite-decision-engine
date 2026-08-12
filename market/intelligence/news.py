"""News sentiment service — powered by real RSS feeds and NVIDIA LLM."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

RSS_URLS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]

# US Fed/macro-economic news relevant to risk assets broadly (crypto included)
# -- separate from RSS_URLS above, which is purely crypto-focused and would
# never surface a pure "Fed holds rates steady" headline (no coin ticker to
# match against SYMBOL_KEYWORDS). Both URLs verified live 2026-08-11: the
# Fed's own press-release feed (authoritative, low volume) and MarketWatch's
# general top-stories feed (higher volume, broader finance coverage --
# MACRO_KEYWORDS below filters it down to what's actually macro-relevant).
MACRO_RSS_URLS = [
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://feeds.marketwatch.com/marketwatch/topstories/",
]

MACRO_KEYWORDS = [
    "federal reserve", "fed ", "fomc", "powell", "interest rate", "rate decision",
    "rate cut", "rate hike", "cpi", "inflation", "jobs report", "nonfarm payrolls",
    "unemployment rate", "gdp",
]

# Keyword sets per symbol -- covers config.py's FIXED_COIN_UNIVERSE (25
# coins) plus DOGE (kept for backward compatibility, not part of the fixed
# universe but harmless to still recognize). Short/generic tickers that are
# also common English words ("uni", "op", "pol", "near", "mkr" as bare
# words) are deliberately left out in favor of the project/company name
# alone, to avoid false-positive matches on unrelated headlines -- matches
# this file's existing convention for the original 10 symbols.
SYMBOL_KEYWORDS: dict[str, list[str]] = {
    "BTC": ["btc", "bitcoin"],
    "ETH": ["eth", "ethereum"],
    "SOL": ["sol", "solana"],
    "BNB": ["bnb", "binance"],
    "XRP": ["xrp", "ripple"],
    "ADA": ["ada", "cardano"],
    "DOGE": ["doge", "dogecoin"],
    "AVAX": ["avax", "avalanche"],
    "DOT": ["dot", "polkadot"],
    "LINK": ["link", "chainlink"],
    "TON": ["ton", "toncoin"],
    "TRX": ["trx", "tron"],
    "SUI": ["sui"],
    "ARB": ["arb", "arbitrum"],
    "OP": ["optimism"],
    "POL": ["polygon", "matic"],
    "UNI": ["uniswap"],
    "AAVE": ["aave"],
    "MKR": ["mkr", "makerdao"],
    "LDO": ["ldo", "lido"],
    "LTC": ["ltc", "litecoin"],
    "BCH": ["bch", "bitcoin cash"],
    "ATOM": ["atom", "cosmos"],
    "NEAR": ["near protocol"],
    "TAO": ["tao", "bittensor"],
    "APT": ["apt", "aptos"],
}

# Prominent crypto-focused VC/institutional investors -- used to detect
# project-funding headlines ("Project X raises $Y from Binance Labs").
# Pure keyword matching, no LLM call.
VC_INSTITUTIONS = [
    "binance labs",
    "a16z",
    "andreessen horowitz",
    "coinbase ventures",
    "paradigm",
    "pantera capital",
    "multicoin capital",
    "polychain capital",
    "jump crypto",
]

_FUNDING_KEYWORDS = [
    "raises", "raised", "funding", "investment", "invests", "backs", "backed",
    "leads round", "led a round", "seed round", "series a", "series b",
]


class NewsService:
    """Provide news sentiment analysis from real news sources."""

    def _rule_based_sentiment(self, headline: str) -> str:
        """Fallback simple sentiment classifier based on keyword heuristic."""
        text = headline.lower()
        pos_words = ["surge", "bull", "gain", "up", "rise", "grow", "rally", "high", "positive", "accumulate", "boost", "support", "skyrocket", "profit", "win", "adopt", "launch", "breakout"]
        neg_words = ["crash", "bear", "drop", "down", "fall", "decline", "sell", "low", "negative", "liquidate", "drain", "resistance", "plunge", "loss", "lose", "ban", "hack", "scam", "lawsuit", "fud"]

        # Word-boundary match, allowing a short inflectional suffix (surge ->
        # surges/surging) -- plain substring containment false-positives on
        # common words (e.g. "up" inside "update", "low" inside "below"), but
        # an exact \bword\b match misses the inflected forms real headlines
        # actually use. \w{0,3} covers -s/-es/-ed/-ing while the leading \b
        # still keeps "update"/"below" excluded (no boundary before "up"/"low"
        # there to begin with).
        pos_count = sum(1 for w in pos_words if re.search(rf"\b{re.escape(w)}\w{{0,3}}\b", text))
        neg_count = sum(1 for w in neg_words if re.search(rf"\b{re.escape(w)}\w{{0,3}}\b", text))

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"

    def _fetch_rss_items(self, url: str) -> list[dict[str, str]]:
        """Fetch RSS feed via requests and parse items using built-in xml.etree.ElementTree."""
        items_list = []
        try:
            # RSS feeds sometimes block empty User-Agent, so we supply a browser-like agent
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    title_node = item.find("title")
                    pub_date_node = item.find("pubDate")

                    title = title_node.text.strip() if title_node is not None and title_node.text else ""
                    pub_date = pub_date_node.text.strip() if pub_date_node is not None and pub_date_node.text else ""

                    if title:
                        items_list.append({
                            "title": title,
                            "published": pub_date
                        })
        except Exception as e:
            logger.warning("Failed to fetch or parse RSS feed from %s: %s", url, e)
        return items_list

    def fetch_rss_feeds(self) -> list[dict[str, str]]:
        """Fetch all configured RSS feeds once and return the combined raw entries.

        Public so a batch caller (e.g. the periodic news job) can fetch once
        per cycle and reuse the same entries across every symbol's
        filtering/sentiment pass, instead of each symbol re-fetching the
        same 2 feeds from scratch.
        """
        all_entries: list[dict[str, str]] = []
        for url in RSS_URLS:
            all_entries.extend(self._fetch_rss_items(url))
        return all_entries

    def fetch_macro_rss_feeds(self) -> list[dict[str, str]]:
        """Fetch all configured US Fed/macro RSS feeds once, same fetch-once-
        per-cycle rationale as fetch_rss_feeds() above -- a separate method
        (not merged into RSS_URLS) since macro headlines route through
        is_macro_headline() rather than SYMBOL_KEYWORDS matching.
        """
        all_entries: list[dict[str, str]] = []
        for url in MACRO_RSS_URLS:
            all_entries.extend(self._fetch_rss_items(url))
        return all_entries

    def is_macro_headline(self, headline: str) -> bool:
        """True if this headline looks like US Fed/macro-economic news
        relevant to risk assets broadly, based on MACRO_KEYWORDS.
        """
        title_lower = headline.lower()
        return any(kw in title_lower for kw in MACRO_KEYWORDS)

    def match_headline_to_symbols(self, headline: str, symbols: list[str] | None = None) -> list[str]:
        """Return which of `symbols` (default: all of SYMBOL_KEYWORDS) this headline mentions.

        Word-boundary match, same false-positive-avoidance rationale as the
        original single-symbol filtering in `analyze()`.
        """
        universe = symbols if symbols is not None else list(SYMBOL_KEYWORDS.keys())
        title_lower = headline.lower()
        matched = []
        for sym in universe:
            kw_list = SYMBOL_KEYWORDS.get(sym.upper())
            if not kw_list:
                continue
            if any(re.search(rf"\b{re.escape(kw)}\b", title_lower) for kw in kw_list):
                matched.append(sym.upper())
        return matched

    def detect_vc_funding(self, headline: str) -> list[str]:
        """Return matched VC/institution names if this headline looks like a
        project-funding announcement, else an empty list.

        Pure keyword matching (institution name + a funding-related word) --
        no LLM call, so this is effectively free to run on every headline.
        """
        title_lower = headline.lower()
        if not any(re.search(rf"\b{re.escape(kw)}", title_lower) for kw in _FUNDING_KEYWORDS):
            return []
        return [inst for inst in VC_INSTITUTIONS if inst in title_lower]

    def classify_sentiment(self, headlines: list[str]) -> dict[str, str]:
        """Classify sentiment for a batch of headlines in as few LLM calls as
        possible (one batched prompt for all of them), falling back to the
        rule-based classifier per-headline on any failure.

        Returns a dict keyed by the headline's lowercased, stripped text --
        callers should look up with `headline.strip().lower()`.
        """
        result: dict[str, str] = {}
        if not headlines:
            return result

        sentiment_mapped: dict[str, str] = {}
        try:
            from services.ai.provider_factory import create_provider
            provider = create_provider()
            if provider and getattr(provider, "_api_key", None):
                headlines_bullet_str = "\n".join(f"- {h}" for h in headlines)
                prompt = f"""Analyze the sentiment of the following crypto news headlines.
For each headline, provide a sentiment label: "positive", "neutral", or "negative".

Headlines:
{headlines_bullet_str}

Respond with a JSON list of objects, each containing exactly "headline" and "sentiment" keys.
Example:
[
  {{"headline": "Bitcoin surges past $60k", "sentiment": "positive"}}, {{"headline": "Market is sideways", "sentiment": "neutral"}}
]
Do not include any other text, explainers, or Markdown block markers like ```json. Output ONLY the raw JSON list of objects.
"""
                res = provider.generate(prompt)
                if res and res.content:
                    content_clean = res.content.strip()
                    if content_clean.startswith("```"):
                        lines = content_clean.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines[-1].startswith("```"):
                            lines = lines[:-1]
                        content_clean = "\n".join(lines).strip()

                    parsed_list = json.loads(content_clean)
                    if isinstance(parsed_list, list):
                        for item in parsed_list:
                            h_title = item.get("headline")
                            sent = str(item.get("sentiment", "neutral")).lower()
                            if sent not in ("positive", "neutral", "negative"):
                                sent = "neutral"
                            if h_title:
                                sentiment_mapped[h_title.strip().lower()] = sent
        except Exception as e:
            logger.info("NVIDIA sentiment provider failed or unavailable, using rule-based fallback: %s", e)

        for h in headlines:
            key = h.strip().lower()
            result[key] = sentiment_mapped.get(key) or self._rule_based_sentiment(h)
        return result

    def classify_and_score(self, headlines: list[str]) -> dict[str, dict[str, Any]]:
        """Classify sentiment AND an impact score for a batch of headlines in
        one batched NVIDIA call (same batching discipline as
        classify_sentiment() above -- one prompt for all headlines, not one
        call per headline).

        Deliberately does NOT ask for translation here -- see
        translate_to_turkish(), a separate non-NVIDIA step, so translation
        keeps working even when NVIDIA is rate-limited/down and vice versa.

        Returns a dict keyed by the headline's lowercased, stripped text
        (same convention as classify_sentiment()), each value
        {"sentiment": "positive"|"neutral"|"negative", "score": int 0-100}.
        """
        result: dict[str, dict[str, Any]] = {}
        if not headlines:
            return result

        mapped: dict[str, dict[str, Any]] = {}
        try:
            from services.ai.provider_factory import create_provider
            provider = create_provider()
            if provider and getattr(provider, "_api_key", None):
                headlines_bullet_str = "\n".join(f"- {h}" for h in headlines)
                prompt = f"""Analyze the sentiment and market impact of the following crypto news headlines.
For each headline, provide:
- "sentiment": "positive", "neutral", or "negative"
- "score": an integer from 0 to 100 for how market-moving/impactful the
  headline is. 0 means routine news with no real price impact; 100 means a
  major market-moving event (e.g. a central bank rate decision, a major
  exchange hack, a landmark regulatory ruling). Most ordinary headlines
  should score well below 50.

Headlines:
{headlines_bullet_str}

Respond with a JSON list of objects, each containing exactly "headline", "sentiment", and "score" keys.
Example:
[
  {{"headline": "Bitcoin surges past $60k", "sentiment": "positive", "score": 55}},
  {{"headline": "Market is sideways", "sentiment": "neutral", "score": 5}}
]
Do not include any other text, explainers, or Markdown block markers like
```json. Output ONLY the raw JSON list of objects.
"""
                res = provider.generate(prompt)
                if res and res.content:
                    content_clean = res.content.strip()
                    if content_clean.startswith("```"):
                        lines = content_clean.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines[-1].startswith("```"):
                            lines = lines[:-1]
                        content_clean = "\n".join(lines).strip()

                    parsed_list = json.loads(content_clean)
                    if isinstance(parsed_list, list):
                        for item in parsed_list:
                            h_title = item.get("headline")
                            sent = str(item.get("sentiment", "neutral")).lower()
                            if sent not in ("positive", "neutral", "negative"):
                                sent = "neutral"
                            try:
                                score = int(item.get("score", 50))
                            except (TypeError, ValueError):
                                score = 50
                            score = max(0, min(100, score))
                            if h_title:
                                mapped[h_title.strip().lower()] = {"sentiment": sent, "score": score}
        except Exception as e:
            logger.info("NVIDIA scoring provider failed or unavailable, using rule-based fallback: %s", e)

        for h in headlines:
            key = h.strip().lower()
            if key in mapped:
                result[key] = mapped[key]
            else:
                # Honest fallback: a real sentiment label from the existing
                # rule-based classifier, but an "unknown impact" default
                # score rather than a fabricated confidence number.
                result[key] = {"sentiment": self._rule_based_sentiment(h), "score": 50}
        return result

    def translate_to_turkish(self, text: str) -> str:
        """Translate a headline to Turkish via a free, dedicated translation
        library -- deliberately NOT NVIDIA or any other LLM chat-completion
        call (see classify_and_score() above for why: translation is a
        well-solved, judgment-free problem, unlike sentiment/impact scoring,
        and keeping it off NVIDIA means it keeps working even when NVIDIA is
        rate-limited/down).

        Falls back to the original English text on any failure -- never
        fabricates a translation.
        """
        if not text.strip():
            return text
        try:
            from deep_translator import GoogleTranslator
            translated = GoogleTranslator(source="en", target="tr").translate(text)
            if translated and translated.strip():
                return translated
        except Exception as e:
            logger.info("Translation failed, falling back to original English text: %s", e)
        return text

    def analyze(
        self,
        symbol: str,
        price: float = 0.0,
        price_change_24h: float | None = None,
        btc_trend: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch headlines from real crypto RSS feeds and classify sentiment using NVIDIA LLM or rules."""
        articles: list[dict[str, Any]] = []

        # 1. Fetch from real public RSS feeds (CoinTelegraph, CoinDesk)
        all_entries = self.fetch_rss_feeds()

        # 2. Case-insensitive filtering of relevant news
        kw_list = SYMBOL_KEYWORDS.get(symbol.upper(), [symbol.lower()])
        filtered_headlines = []
        seen_titles = set()

        for entry in all_entries:
            title = entry.get("title", "")
            if not title:
                continue

            title_clean = title.strip()
            if title_clean in seen_titles:
                continue

            title_lower = title_clean.lower()
            # Word-boundary match -- plain substring containment false-positives
            # on short keywords like "eth"/"ada"/"sol" inside unrelated words
            # ("method", "Canada", "consolidate").
            if any(re.search(rf"\b{re.escape(kw)}\b", title_lower) for kw in kw_list):
                seen_titles.add(title_clean)
                published = entry.get("published")
                if not published:
                    published = datetime.now(UTC).isoformat()

                filtered_headlines.append({
                    "source": "RSS",
                    "headline": title_clean,
                    "timestamp": published,
                })

        # Fallback to general market news if no symbol-specific news was found
        if not filtered_headlines and all_entries:
            logger.info("No symbol-specific news found for %s, falling back to general market news", symbol)
            for entry in all_entries:
                title = entry.get("title", "")
                if not title:
                    continue
                title_clean = title.strip()
                if title_clean in seen_titles:
                    continue
                seen_titles.add(title_clean)
                published = entry.get("published")
                if not published:
                    published = datetime.now(UTC).isoformat()

                filtered_headlines.append({
                    "source": "RSS_GENERAL",
                    "headline": title_clean,
                    "timestamp": published,
                })

                if len(filtered_headlines) >= 5:
                    break

        # Limit to 5 headlines for token budget and response time
        filtered_headlines = filtered_headlines[:5]

        # 3. Classify sentiment using existing NVIDIA NIM LLM or fallback rules
        if filtered_headlines:
            sentiment_by_headline = self.classify_sentiment([h["headline"] for h in filtered_headlines])
            for h in filtered_headlines:
                headline_title = h["headline"]
                sentiment = sentiment_by_headline.get(headline_title.strip().lower(), "neutral")

                relevance = 0.8 if h["source"] == "RSS" else 0.4
                articles.append({
                    "source": "RSS_FEED",
                    "headline": headline_title,
                    "sentiment": sentiment,
                    "relevance": relevance,
                    "timestamp": h["timestamp"],
                })

        # 4. Backward Compatibility: Append simulated price-based/trend headlines if requested or if no RSS articles
        if price_change_24h is not None and abs(price_change_24h) > 2:
            direction = "positive" if price_change_24h > 0 else "negative"
            articles.append({
                "source": "market_data",
                "headline": f"{symbol} moved {abs(price_change_24h):.1f}% in 24h",
                "sentiment": direction,
                "relevance": 0.8,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        if btc_trend:
            trend_label = btc_trend.lower()
            articles.append({
                "source": "market_data",
                "headline": f"BTC trend is {trend_label}",
                "sentiment": "positive" if btc_trend == "BULLISH" else "negative" if btc_trend == "BEARISH" else "neutral",
                "relevance": 0.5,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return articles

    def sentiment_score(self, articles: list[dict[str, Any]]) -> float:
        """Calculate overall sentiment score from -1.0 (extremely bearish) to 1.0 (extremely bullish)."""
        if not articles:
            return 0.0
        scores = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        total = sum(scores.get(a.get("sentiment", "neutral"), 0) * a.get("relevance", 0.5) for a in articles)
        max_possible = sum(a.get("relevance", 0.5) for a in articles)
        if max_possible == 0:
            return 0.0
        return round(total / max_possible, 4)


def headline_hash(headline: str) -> str:
    """Stable dedup key for a headline, used with database.SentAlert."""
    return hashlib.sha256(headline.strip().lower().encode("utf-8")).hexdigest()
