"""Tests for NewsService's symbol-relevance filter and rule-based sentiment
classifier -- both previously used unanchored substring matching, causing
false positives on short keywords/sentiment words embedded in unrelated
words. No test coverage existed for this file before.

Also covers the v2 additions: classify_and_score() (batched sentiment +
impact score), translate_to_turkish() (non-NVIDIA), and is_macro_headline()
(US Fed/macro keyword filter) -- see
SPRINT_JULES_NEWS_BOT_V2_SCORE_TRANSLATE_MACRO.md.
"""

from unittest.mock import MagicMock, patch

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

    def test_negated_negative_word_reads_as_positive(self):
        # Real reported bug 2026-08-21: "won't drop" contains "drop" (a
        # neg_word) with no negation handling at all, so this was
        # classified negative despite being a bullish headline.
        service = NewsService()
        assert service._rule_based_sentiment(
            "Nansen founder says BTC won't drop below $60K"
        ) == "positive"

    def test_negated_positive_word_reads_as_negative(self):
        service = NewsService()
        assert service._rule_based_sentiment(
            "Analyst warns Bitcoin is unlikely to rally this quarter"
        ) == "negative"

    def test_double_negative_still_reads_correctly_per_nearest_negation(self):
        # A negation far earlier in a long headline shouldn't flip a
        # keyword it isn't actually governing -- window is intentionally
        # short (~25 chars).
        service = NewsService()
        result = service._rule_based_sentiment(
            "Analyst who was not always right about markets says Bitcoin will surge"
        )
        assert result == "positive"


class TestClassifyAndScore:
    def test_empty_headlines_returns_empty_dict(self):
        service = NewsService()
        assert service.classify_and_score([]) == {}

    @patch("services.ai.provider_factory.create_provider")
    def test_successful_llm_response_parsed_into_sentiment_and_score(self, mock_create_provider):
        # Matched back by "index", not headline text -- see the module
        # docstring on why (an LLM paraphrasing the headline in its response
        # used to silently drop it into the rule-based fallback).
        mock_provider = MagicMock()
        mock_provider._api_key = "test_key"
        mock_provider.generate.return_value = MagicMock(
            content=(
                '[{"index": 0, "sentiment": "positive", "score": 55, "reason": "Big rally"}, '
                '{"index": 1, "sentiment": "neutral", "score": 5, "reason": "Nothing new"}]'
            )
        )
        mock_create_provider.return_value = mock_provider

        result = NewsService().classify_and_score(["Bitcoin surges past $60k", "Market is sideways"])

        assert result["bitcoin surges past $60k"] == {"sentiment": "positive", "score": 55, "reason": "Big rally"}
        assert result["market is sideways"] == {"sentiment": "neutral", "score": 5, "reason": "Nothing new"}
        # exactly one batched call for both headlines, not one per headline
        mock_provider.generate.assert_called_once()

    @patch("services.ai.provider_factory.create_provider")
    def test_llm_response_matched_by_index_even_when_headline_text_is_paraphrased(self, mock_create_provider):
        mock_provider = MagicMock()
        mock_provider._api_key = "test_key"
        # The LLM slightly reworded the headline in its own output -- this
        # must still match via "index", not fall through to the rule-based
        # fallback the way lowercased-text matching used to.
        mock_provider.generate.return_value = MagicMock(
            content='[{"index": 0, "sentiment": "positive", "score": 70, "reason": "Strong signal"}]'
        )
        mock_create_provider.return_value = mock_provider

        result = NewsService().classify_and_score(["BTC won't drop below $60K, says Nansen founder"])

        assert result["btc won't drop below $60k, says nansen founder"] == {
            "sentiment": "positive", "score": 70, "reason": "Strong signal",
        }

    @patch("services.ai.provider_factory.create_provider")
    def test_score_clamped_to_0_100_range(self, mock_create_provider):
        mock_provider = MagicMock()
        mock_provider._api_key = "test_key"
        mock_provider.generate.return_value = MagicMock(
            content='[{"index": 0, "sentiment": "positive", "score": 999, "reason": "x"}]'
        )
        mock_create_provider.return_value = mock_provider

        result = NewsService().classify_and_score(["Big news"])
        assert result["big news"]["score"] == 100

    @patch("services.ai.provider_factory.create_provider")
    def test_malformed_json_falls_back_to_rule_based_with_neutral_score(self, mock_create_provider):
        mock_provider = MagicMock()
        mock_provider._api_key = "test_key"
        mock_provider.generate.return_value = MagicMock(content="not valid json at all")
        mock_create_provider.return_value = mock_provider

        result = NewsService().classify_and_score(["Bitcoin surges as bulls rally"])

        assert result["bitcoin surges as bulls rally"] == {"sentiment": "positive", "score": 50, "reason": None}

    def test_no_provider_falls_back_to_rule_based_with_neutral_score(self):
        with _NO_LLM:
            result = NewsService().classify_and_score(["Market crash triggers panic sell-off"])

        assert result["market crash triggers panic sell-off"] == {"sentiment": "negative", "score": 50, "reason": None}


class TestTranslateToTurkish:
    def test_blank_text_returned_unchanged(self):
        service = NewsService()
        assert service.translate_to_turkish("   ") == "   "

    @patch("deep_translator.GoogleTranslator.translate")
    def test_successful_translation_returned(self, mock_translate):
        mock_translate.return_value = "Bitcoin 60 bin doları geçti"
        result = NewsService().translate_to_turkish("Bitcoin surges past $60k")
        assert result == "Bitcoin 60 bin doları geçti"

    @patch("deep_translator.GoogleTranslator.translate")
    def test_translation_failure_falls_back_to_original_text(self, mock_translate):
        mock_translate.side_effect = Exception("network error")
        original = "Bitcoin surges past $60k"
        result = NewsService().translate_to_turkish(original)
        assert result == original

    @patch("deep_translator.GoogleTranslator.translate")
    def test_protected_brand_name_survives_translation(self, mock_translate):
        # Real reported bug 2026-08-21: "MicroStrategy" was showing up
        # translated in Turkish alerts (confusing, and risks breaking
        # downstream symbol matching against MSTR/BTC).
        mock_translate.side_effect = lambda *a: a[-1].replace("sold", "sattı")
        result = NewsService().translate_to_turkish("MicroStrategy sold 1690 BTC today")
        assert "MicroStrategy" in result
        assert "Strateji" not in result
        called_with = mock_translate.call_args[0][-1]
        assert "MicroStrategy" not in called_with  # confirms a placeholder was actually used

    @patch("deep_translator.GoogleTranslator.translate")
    def test_protected_term_strategy_survives_translation(self, mock_translate):
        # "Strategy" (the company's current, rebranded name) is also an
        # ordinary English word -- the real observed failure was Google
        # Translate literal-translating it to "Strateji".
        mock_translate.side_effect = lambda *a: a[-1].replace("sold", "sattı")
        result = NewsService().translate_to_turkish("Strategy sold 1690 Bitcoin")
        assert "Strategy" in result
        assert "Strateji" not in result

    @patch("deep_translator.GoogleTranslator.translate")
    def test_empty_translation_result_falls_back_to_original_text(self, mock_translate):
        mock_translate.return_value = ""
        original = "Bitcoin surges past $60k"
        result = NewsService().translate_to_turkish(original)
        assert result == original


class TestIsMacroHeadline:
    def test_fed_keyword_matches(self):
        service = NewsService()
        assert service.is_macro_headline("Fed holds interest rates steady") is True
        assert service.is_macro_headline("Powell signals no near-term rate cuts") is True
        assert service.is_macro_headline("CPI report shows inflation cooling") is True

    def test_unrelated_headline_does_not_match(self):
        service = NewsService()
        assert service.is_macro_headline("Bitcoin surges past $60k") is False
        assert service.is_macro_headline("Local sports team wins championship") is False

    def test_fed_administrative_noise_does_not_match(self):
        # Real reported bug 2026-08-21: headlines that mention "Federal
        # Reserve"/"Fed" purely as the organization involved in routine
        # HR/legal news (not an actual rate decision) were reaching the
        # Telegram feed tagged "BTC (Genel Piyasa)" with ~0% market impact.
        service = NewsService()
        assert service.is_macro_headline(
            "Federal Reserve settles lawsuit with former employee"
        ) is False
        assert service.is_macro_headline(
            "Regional Fed bank approves merger with community bank"
        ) is False
        assert service.is_macro_headline(
            "Fed official resigns amid personnel review"
        ) is False

    def test_real_rate_decision_still_matches_even_with_powell_mentioned(self):
        # Sanity check the noise filter isn't so broad it also excludes
        # genuine rate-decision news just because it names an official.
        service = NewsService()
        assert service.is_macro_headline(
            "Powell announces Fed will hold interest rates steady"
        ) is True
