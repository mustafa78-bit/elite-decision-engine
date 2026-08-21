"""News sentiment service — powered by real RSS feeds and NVIDIA LLM."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

import requests

from config import INTELLIGENCE_CACHE_TTL_SECONDS

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

# A headline can match MACRO_KEYWORDS purely on organization name (e.g. any
# Fed press release, or a MarketWatch story that happens to mention "interest
# rate" in passing) without actually being about a market-moving decision --
# the Fed's own press-release feed mixes real FOMC/rate-decision news with
# routine HR/legal/administrative releases (ex-employee lawsuits, personnel
# changes, small-bank merger approvals) that have ~0% crypto market impact.
# Confirmed live 2026-08-21: exactly this class of headline was reaching the
# Telegram feed tagged "BTC (Genel Piyasa)". Checked second, after
# MACRO_KEYWORDS already matched -- any hit here vetoes the headline.
MACRO_NOISE_KEYWORDS = [
    "lawsuit", "ex-employee", "former employee", "misconduct", "settlement",
    "resigns", "retires", "appoints", "appointment", "promotion", "personnel",
    "enforcement action", "internal review", "disciplinary", "harassment",
    "discrimination", "wrongful termination", "bank application",
    "merger", "acquisition of", "branch closure", "community bank",
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

# Brand/company names that must survive translate_to_turkish() unchanged --
# see that method's docstring. "Strategy" is included deliberately even
# though it's also an ordinary English word: it's the real, current name
# crypto news headlines use for the company formerly known as
# MicroStrategy, and literal-translating it to "Strateji" was a confirmed
# live bug. The trade-off (a headline about "the Fed's strategy" would also
# keep the English word "Strategy" untranslated) is accepted as minor and
# rare next to the company-name case, which appears in real crypto
# headlines constantly.
_TRANSLATION_PROTECTED_TERMS = [
    "MicroStrategy", "Strategy", "BlackRock", "Grayscale", "Bullish",
    "Coinbase", "Binance", "Kraken", "Bitfinex", "Bitstamp", "Fidelity",
    "VanEck", "Ark Invest", "Galaxy Digital", "Tether", "Circle",
    "Chainlink", "Uniswap", "Aave", "MakerDAO", "Lido", "Nansen",
    "Bloomberg", "CoinDesk", "Cointelegraph", "Reuters",
]


# Feed domain -> human-readable name, for the "Kaynak: X" line in the
# Telegram alert. Falls back to the bare domain for anything not listed
# here (e.g. a feed added later) rather than failing.
_SOURCE_DISPLAY_NAMES: dict[str, str] = {
    "cointelegraph.com": "Cointelegraph",
    "coindesk.com": "CoinDesk",
    "federalreserve.gov": "Federal Reserve",
    "marketwatch.com": "MarketWatch",
}


def source_display_name(url: str) -> str:
    from urllib.parse import urlparse
    netloc = urlparse(url).netloc.replace("www.", "")
    for domain, name in _SOURCE_DISPLAY_NAMES.items():
        if domain in netloc:
            return name
    return netloc


class NewsService:
    """Provide news sentiment analysis from real news sources."""

    # classify_sentiment() already batches one symbol's own headlines into a
    # single NVIDIA call, but nothing shared the result *across* symbols --
    # a symbol with no news of its own falls back to the same 5 general
    # market headlines every other news-less symbol also falls back to, so
    # a 25-symbol scan could re-classify that identical headline set up to
    # ~15-20 times, once per symbol, for an answer that can't differ between
    # them. Cache keyed by the exact (sorted) headline set, class-level so it
    # collapses calls across separate NewsService() instances too -- same
    # pattern as IntelligenceService/WhaleService's caches.
    _sentiment_cache: dict[str, tuple[float, dict[str, str]]] = {}
    _sentiment_cache_lock = threading.Lock()

    # Words/phrases that flip the polarity of a sentiment keyword appearing
    # shortly after them ("won't drop", "unlikely to crash", "no longer
    # bearish") -- the plain keyword-count heuristic below had no negation
    # handling at all, which is exactly why headlines like "Nansen founder
    # says BTC won't drop below $60K" (contains "drop", a neg_word, negated)
    # were misclassified negative. Confirmed live 2026-08-21.
    _NEGATION_TRIGGERS = (
        "won't", "wont", "will not", "not ", "no longer", "unlikely to",
        "isn't", "wasn't", "aren't", "never", "doesn't", "didn't", "without",
        "denies", "denied", "refutes", "refuted", "fails to", "failed to",
    )

    def _is_negated(self, text: str, match_start: int) -> bool:
        # Only look shortly before the match -- a negation trigger far
        # earlier in a long headline is unlikely to still be governing this
        # particular word.
        window = text[max(0, match_start - 25):match_start]
        return any(trig in window for trig in self._NEGATION_TRIGGERS)

    def _rule_based_sentiment(self, headline: str) -> str:
        """Fallback simple sentiment classifier based on keyword heuristic,
        with basic negation handling (see _is_negated above)."""
        text = headline.lower()
        # "resistance"/"support" removed: they're TA jargon whose actual
        # sentiment is context-dependent ("breaking resistance" is bullish,
        # not bearish) -- confirmed live 2026-08-21 as a source of
        # mislabeled headlines, not a reliable polarity signal either way.
        pos_words = ["surge", "bull", "gain", "up", "rise", "grow", "rally", "high", "positive", "accumulate", "boost", "skyrocket", "profit", "win", "adopt", "launch", "breakout"]
        neg_words = ["crash", "bear", "drop", "down", "fall", "decline", "sell", "low", "negative", "liquidate", "drain", "plunge", "loss", "lose", "ban", "hack", "scam", "lawsuit", "fud"]

        # Word-boundary match, allowing a short inflectional suffix (surge ->
        # surges/surging) -- plain substring containment false-positives on
        # common words (e.g. "up" inside "update", "low" inside "below"), but
        # an exact \bword\b match misses the inflected forms real headlines
        # actually use. \w{0,3} covers -s/-es/-ed/-ing while the leading \b
        # still keeps "update"/"below" excluded (no boundary before "up"/"low"
        # there to begin with).
        net = 0
        for w in pos_words:
            for m in re.finditer(rf"\b{re.escape(w)}\w{{0,3}}\b", text):
                net += -1 if self._is_negated(text, m.start()) else 1
        for w in neg_words:
            for m in re.finditer(rf"\b{re.escape(w)}\w{{0,3}}\b", text):
                net += 1 if self._is_negated(text, m.start()) else -1

        if net > 0:
            return "positive"
        elif net < 0:
            return "negative"
        return "neutral"

    def _fetch_rss_items(self, url: str) -> list[dict[str, str]]:
        """Fetch RSS feed via requests and parse items using built-in xml.etree.ElementTree."""
        items_list = []
        source_name = source_display_name(url)
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
                            "published": pub_date,
                            "source_name": source_name,
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
        relevant to risk assets broadly, based on MACRO_KEYWORDS -- and NOT
        administrative/HR/legal Fed noise (MACRO_NOISE_KEYWORDS), which
        matches the same organization-name keywords without being a real
        market-moving event.
        """
        title_lower = headline.lower()
        if not any(kw in title_lower for kw in MACRO_KEYWORDS):
            return False
        return not any(kw in title_lower for kw in MACRO_NOISE_KEYWORDS)

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
        """Classify sentiment for a batch of headlines, reusing a cached
        result for the exact same headline set (regardless of which symbol
        is asking -- see the class-level cache docstring above) before
        falling through to the real, uncached classification.
        """
        if not headlines:
            return {}

        cache_key = hashlib.sha256("|".join(sorted(h.strip().lower() for h in headlines)).encode()).hexdigest()
        cached = NewsService._sentiment_cache.get(cache_key)
        if cached is not None and time.time() - cached[0] < INTELLIGENCE_CACHE_TTL_SECONDS:
            return cached[1]

        with NewsService._sentiment_cache_lock:
            cached = NewsService._sentiment_cache.get(cache_key)
            if cached is not None and time.time() - cached[0] < INTELLIGENCE_CACHE_TTL_SECONDS:
                return cached[1]
            result = self._classify_sentiment_uncached(headlines)
            NewsService._sentiment_cache[cache_key] = (time.time(), result)
            return result

    def _classify_sentiment_uncached(self, headlines: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        # Keyed by index into `headlines`, not by headline text -- an LLM
        # will often paraphrase/normalize a headline in its JSON output
        # despite instructions not to, and matching back by lowercased text
        # then silently dropped any headline it touched into the rule-based
        # fallback as if the whole call had failed. Confirmed live
        # 2026-08-21 as a real, frequent cause of the fallback firing (and
        # therefore of the fallback's generic score/sentiment showing up far
        # more than intended). An integer index round-trips through JSON
        # exactly, with nothing to paraphrase.
        sentiment_mapped: dict[int, str] = {}
        try:
            from services.ai.provider_factory import get_shared_provider
            provider = get_shared_provider()
            if provider and getattr(provider, "_api_key", None):
                headlines_numbered = "\n".join(f"{i}: {h}" for i, h in enumerate(headlines))
                prompt = f"""Analyze the sentiment of the following crypto news headlines, given by index.
For each headline, respond with its index number and a sentiment label: "positive", "neutral", or "negative".

Headlines:
{headlines_numbered}

Respond with a JSON list of objects, each containing exactly "index" (the integer given above, unchanged) and "sentiment" keys.
Example:
[
  {{"index": 0, "sentiment": "positive"}}, {{"index": 1, "sentiment": "neutral"}}
]
Include exactly one object per headline above, using its exact index number. Do not include any other text, explainers, or Markdown block markers like ```json. Output ONLY the raw JSON list of objects.
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
                            idx = item.get("index")
                            sent = str(item.get("sentiment", "neutral")).lower()
                            if sent not in ("positive", "neutral", "negative"):
                                sent = "neutral"
                            if isinstance(idx, int) and 0 <= idx < len(headlines):
                                sentiment_mapped[idx] = sent
        except Exception as e:
            logger.info("NVIDIA sentiment provider failed or unavailable, using rule-based fallback: %s", e)

        for i, h in enumerate(headlines):
            key = h.strip().lower()
            result[key] = sentiment_mapped.get(i) or self._rule_based_sentiment(h)
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
        {"sentiment": "positive"|"neutral"|"negative", "score": int 0-100,
        "reason": str | None} -- reason is a short one-line explanation of
        the market impact (used by the Telegram alert's "Özet & Etki" line),
        None when the rule-based fallback fired (it has no reasoning
        capability, so it's honest to leave this empty rather than fabricate
        one).
        """
        result: dict[str, dict[str, Any]] = {}
        if not headlines:
            return result

        # Keyed by index, not headline text -- see the identical comment in
        # _classify_sentiment_uncached() above; this is the path that
        # actually drives the Telegram news alert, so a text-match miss here
        # is exactly what was producing the "nearly everything gets 50"
        # symptom (every miss falls through to the flat fallback score).
        mapped: dict[int, dict[str, Any]] = {}
        try:
            from services.ai.provider_factory import get_shared_provider
            provider = get_shared_provider()
            if provider and getattr(provider, "_api_key", None):
                headlines_numbered = "\n".join(f"{i}: {h}" for i, h in enumerate(headlines))
                prompt = f"""Analyze the sentiment and market impact of the following crypto news headlines, given by index.
For each headline, provide:
- "index": the integer given below, unchanged
- "sentiment": "positive", "neutral", or "negative"
- "score": an integer from 0 to 100 for how market-moving/impactful the
  headline is. 0 means routine news with no real price impact; 100 means a
  major market-moving event (e.g. a central bank rate decision, a major
  exchange hack, a landmark regulatory ruling). Most ordinary headlines
  should score well below 50. As a rough guide: Fed rate decisions, >$100M
  ETF flows, exchange hacks, and major regulatory rulings score 75-100;
  corporate treasury purchases (e.g. a company buying Bitcoin) and clear
  technical breakouts score 45-74; analyst opinions, price predictions, and
  routine exchange listings score 0-44.
- "reason": ONE short sentence (max ~15 words) explaining WHY this headline
  matters for the market, not a restatement of the headline itself -- e.g.
  "Increases institutional demand and reduces exchange supply" rather than
  "A company bought Bitcoin".

Headlines:
{headlines_numbered}

Respond with a JSON list of objects, each containing exactly "index", "sentiment", "score", and "reason" keys.
Example:
[
  {{"index": 0, "sentiment": "positive", "score": 55, "reason": "Large corporate purchase reduces available exchange supply"}},
  {{"index": 1, "sentiment": "neutral", "score": 5, "reason": "Routine market commentary with no new information"}}
]
Include exactly one object per headline above, using its exact index number. Do not include any other text, explainers, or Markdown block markers like
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
                            idx = item.get("index")
                            sent = str(item.get("sentiment", "neutral")).lower()
                            if sent not in ("positive", "neutral", "negative"):
                                sent = "neutral"
                            try:
                                score = int(item.get("score", 50))
                            except (TypeError, ValueError):
                                score = 50
                            score = max(0, min(100, score))
                            reason = item.get("reason")
                            reason = reason.strip() if isinstance(reason, str) and reason.strip() else None
                            if isinstance(idx, int) and 0 <= idx < len(headlines):
                                mapped[idx] = {"sentiment": sent, "score": score, "reason": reason}
        except Exception as e:
            logger.info("NVIDIA scoring provider failed or unavailable, using rule-based fallback: %s", e)

        for i, h in enumerate(headlines):
            key = h.strip().lower()
            if i in mapped:
                result[key] = mapped[i]
            else:
                # Honest fallback: a real sentiment label from the existing
                # rule-based classifier, but an "unknown impact" default
                # score rather than a fabricated confidence number, and no
                # reason (the rule-based classifier can't explain itself).
                result[key] = {"sentiment": self._rule_based_sentiment(h), "score": 50, "reason": None}
        return result

    def translate_to_turkish(self, text: str) -> str:
        """Translate a headline to Turkish via a free, dedicated translation
        library -- deliberately NOT NVIDIA or any other LLM chat-completion
        call (see classify_and_score() above for why: translation is a
        well-solved, judgment-free problem, unlike sentiment/impact scoring,
        and keeping it off NVIDIA means it keeps working even when NVIDIA is
        rate-limited/down).

        Protected brand/proper-noun terms (_TRANSLATION_PROTECTED_TERMS) are
        swapped for placeholder tokens before translating and restored
        after -- Google Translate has no way to know "Strategy" (the
        company Michael Saylor's MicroStrategy rebranded to) is a proper
        noun rather than the common English word, and was literally
        translating it to "Strateji". Confirmed live 2026-08-21 that a
        short alphanumeric placeholder like "Q3Q" survives GoogleTranslator
        unchanged where the real word would not.

        Falls back to the original English text on any failure -- never
        fabricates a translation.
        """
        if not text.strip():
            return text
        try:
            from deep_translator import GoogleTranslator

            working_text = text
            protected_map: dict[str, str] = {}
            for i, term in enumerate(_TRANSLATION_PROTECTED_TERMS):
                pattern = rf"\b{re.escape(term)}\b"
                if re.search(pattern, working_text, re.IGNORECASE):
                    placeholder = f"Q{i}Q"
                    working_text = re.sub(pattern, placeholder, working_text, flags=re.IGNORECASE)
                    protected_map[placeholder] = term

            translated = GoogleTranslator(source="en", target="tr").translate(working_text)
            if translated and translated.strip():
                for placeholder, term in protected_map.items():
                    translated = translated.replace(placeholder, term)
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
