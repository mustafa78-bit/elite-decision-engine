"""Tests for NewsService's symbol-relevance filter and rule-based sentiment
classifier -- both previously used unanchored substring matching, causing
false positives on short keywords/sentiment words embedded in unrelated
words. No test coverage existed for this file before.
"""

from unittest.mock import patch

from market.intelligence.news import NewsService

_NO_LLM = patch("services.ai.provider_factory.create_provider", return_value=None)


class TestSymbolRelevanceFilter:
    def test_short_keyword_does_not_match_inside_unrelated_word(self):
        entries = [
            {"title": "Fed announces new method for rate hikes", "published": None},
            {"title": "Trudeau of Canada speaks on trade policy", "published": None},
            {"title": "Analysts urge investors to consolidate portfolios", "published": None},
        ]
        service = NewsService()
        with patch.object(service, "_fetch_rss_items", return_value=entries), _NO_LLM:
            eth_articles = service.analyze(symbol="ETH")
            ada_articles = service.analyze(symbol="ADA")
            sol_articles = service.analyze(symbol="SOL")

        # None of these headlines actually mention the symbol -- the keyword
        # filter must not tag any of them as a symbol-specific match
        # (relevance=0.8). It's fine if they still surface via the separate
        # general-market-news fallback (relevance=0.4) -- that's unrelated,
        # pre-existing behavior for when no symbol-specific match exists.
        assert all(a["relevance"] != 0.8 for a in eth_articles)
        assert all(a["relevance"] != 0.8 for a in ada_articles)
        assert all(a["relevance"] != 0.8 for a in sol_articles)

    def test_real_symbol_mention_still_matches(self):
        entries = [
            {"title": "Ethereum price surges after upgrade", "published": None},
            {"title": "Unrelated headline about something else entirely", "published": None},
        ]
        service = NewsService()
        with patch.object(service, "_fetch_rss_items", return_value=entries), _NO_LLM:
            articles = service.analyze(symbol="ETH")

        matched = [a for a in articles if a["relevance"] == 0.8]
        assert len(matched) == 1
        assert "Ethereum" in matched[0]["headline"]


class TestRuleBasedSentiment:
    def test_sentiment_word_does_not_match_inside_unrelated_word(self):
        service = NewsService()
        # "update" contains "up", "below" contains "low", "banking" contains "ban"
        assert service._rule_based_sentiment("Exchange announces protocol update") == "neutral"
        assert service._rule_based_sentiment("Price stays below the current level") == "neutral"
        assert service._rule_based_sentiment("New banking regulations proposed") == "neutral"

    def test_real_sentiment_words_still_classify_correctly(self):
        service = NewsService()
        assert service._rule_based_sentiment("Bitcoin surges as bulls rally") == "positive"
        assert service._rule_based_sentiment("Market crash triggers panic sell-off") == "negative"
