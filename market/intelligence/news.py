"""News sentiment service — powered by real RSS feeds and NVIDIA LLM."""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timezone
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class NewsService:
    """Provide news sentiment analysis from real news sources."""

    def _rule_based_sentiment(self, headline: str) -> str:
        """Fallback simple sentiment classifier based on keyword heuristic."""
        text = headline.lower()
        pos_words = ["surge", "bull", "gain", "up", "rise", "grow", "rally", "high", "positive", "accumulate", "boost", "support", "skyrocket", "profit", "win", "adopt", "launch", "breakout"]
        neg_words = ["crash", "bear", "drop", "down", "fall", "decline", "sell", "low", "negative", "liquidate", "drain", "resistance", "plunge", "loss", "lose", "ban", "hack", "scam", "lawsuit", "fud"]

        # Word-boundary match -- plain substring containment false-positives
        # on common words (e.g. "up" inside "update", "low" inside "below").
        pos_count = sum(1 for w in pos_words if re.search(rf"\b{re.escape(w)}\b", text))
        neg_count = sum(1 for w in neg_words if re.search(rf"\b{re.escape(w)}\b", text))

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
        rss_urls = [
            "https://cointelegraph.com/rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/"
        ]

        all_entries = []
        for url in rss_urls:
            all_entries.extend(self._fetch_rss_items(url))

        # 2. Case-insensitive filtering of relevant news
        symbol_keywords = {
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
        }

        kw_list = symbol_keywords.get(symbol.upper(), [symbol.lower()])
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
        sentiment_mapped = {}
        if filtered_headlines:
            try:
                from services.ai.provider_factory import create_provider
                provider = create_provider()
                if provider and getattr(provider, "_api_key", None):
                    headlines_bullet_str = "\n".join(f"- {h['headline']}" for h in filtered_headlines)
                    prompt = f"""Analyze the sentiment of the following news headlines related to the cryptocurrency {symbol}.
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

            for h in filtered_headlines:
                headline_title = h["headline"]
                sentiment = sentiment_mapped.get(headline_title.strip().lower())
                if not sentiment:
                    sentiment = self._rule_based_sentiment(headline_title)

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
