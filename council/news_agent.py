from __future__ import annotations

import logging
from typing import Any, Optional

from council.base import (
    DIRECTION_BEARISH,
    DIRECTION_BULLISH,
    DIRECTION_NEUTRAL,
    DIRECTION_PASS,
    AgentReport,
    BaseAgent,
)
from execution.pipeline import TradingSignal
from market.intelligence.news import NewsService

logger = logging.getLogger(__name__)


class NewsAgent(BaseAgent):
    """Evaluates news sentiment for the symbol.

    Wraps NewsService to provide sentiment-based trade guidance.
    """

    def __init__(
        self,
        name: str = "News",
        weight: float = 1.0,
        priority: int = 3,
        news_service: Optional[NewsService] = None,
    ) -> None:
        super().__init__(name=name, weight=weight, priority=priority)
        self.news_service = news_service or NewsService()

    def evaluate(
        self,
        signal: Optional[TradingSignal] = None,
        scores: Optional[dict[str, Any]] = None,
        market_data: Optional[Any] = None,
        **kwargs: Any,
    ) -> AgentReport:
        symbol = getattr(signal, "symbol", "?") if signal else "?"
        side = getattr(signal, "side", "LONG") if signal else "LONG"

        btc_trend = kwargs.get("btc_trend")
        intelligence_bundle = kwargs.get("intelligence_bundle")

        news_articles: list[dict[str, Any]] = []

        if intelligence_bundle is not None:
            news_articles = getattr(intelligence_bundle, "news", [])
        else:
            price_change = kwargs.get("price_change_24h")
            try:
                news_articles = self.news_service.analyze(
                    symbol=symbol,
                    price=kwargs.get("price", 0.0),
                    price_change_24h=price_change,
                    btc_trend=btc_trend,
                )
            except Exception as e:
                logger.warning("NewsAgent analysis failed for %s: %s", symbol, e)
                return AgentReport(
                    agent_name=self.name,
                    symbol=symbol,
                    direction=DIRECTION_NEUTRAL,
                    confidence=0.0,
                    score=0.0,
                    reasoning=[f"News fetch failed: {e}"],
                )

        if not news_articles:
            return AgentReport(
                agent_name=self.name,
                symbol=symbol,
                direction=DIRECTION_NEUTRAL,
                confidence=0.0,
                score=0.5,
                reasoning=["No news articles available"],
                data_points={"article_count": 0},
            )

        sentiment_score = self.news_service.sentiment_score(news_articles)
        article_count = len(news_articles)

        reasoning: list[str] = []
        direction = DIRECTION_NEUTRAL
        confidence = 0.5

        if sentiment_score > 0.3:
            direction = DIRECTION_BULLISH
            confidence = min(1.0, sentiment_score)
            reasoning.append(f"Positive news sentiment ({sentiment_score:.2f})")
        elif sentiment_score < -0.3:
            direction = DIRECTION_BEARISH
            confidence = min(1.0, abs(sentiment_score))
            reasoning.append(f"Negative news sentiment ({sentiment_score:.2f})")
        else:
            direction = DIRECTION_NEUTRAL
            confidence = abs(sentiment_score)
            reasoning.append("Neutral news sentiment")

        reasoning.append(f"{article_count} news articles analyzed")

        headlines = [a.get("headline", "") for a in news_articles[:5]]

        return AgentReport(
            agent_name=self.name,
            symbol=symbol,
            direction=direction,
            confidence=round(confidence, 4),
            score=round(float(sentiment_score), 4),
            reasoning=reasoning,
            data_points={
                "sentiment_score": sentiment_score,
                "article_count": article_count,
                "headlines": headlines,
                "articles": news_articles,
            },
        )
