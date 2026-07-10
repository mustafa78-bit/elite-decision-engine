"""News sentiment service — simulated from market conditions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NewsService:
    """Provide news sentiment analysis from available market data."""

    def analyze(
        self,
        symbol: str,
        price: float = 0.0,
        price_change_24h: Optional[float] = None,
        btc_trend: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []

        if price_change_24h is not None and abs(price_change_24h) > 2:
            direction = "positive" if price_change_24h > 0 else "negative"
            articles.append({
                "source": "market_data",
                "headline": f"{symbol} moved {abs(price_change_24h):.1f}% in 24h",
                "sentiment": direction,
                "relevance": 0.8,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        if btc_trend:
            trend_label = btc_trend.lower()
            articles.append({
                "source": "market_data",
                "headline": f"BTC trend is {trend_label}",
                "sentiment": "positive" if btc_trend == "BULLISH" else "negative" if btc_trend == "BEARISH" else "neutral",
                "relevance": 0.5,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return articles

    def sentiment_score(self, articles: list[dict[str, Any]]) -> float:
        if not articles:
            return 0.0
        scores = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        total = sum(scores.get(a.get("sentiment", "neutral"), 0) * a.get("relevance", 0.5) for a in articles)
        max_possible = sum(a.get("relevance", 0.5) for a in articles)
        if max_possible == 0:
            return 0.0
        return round(total / max_possible, 4)
