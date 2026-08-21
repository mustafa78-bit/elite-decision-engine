"""Tests for services/news_job_service.py -- proactive Telegram alerts for
market-moving crypto news, US Fed/macro news, and VC/institutional funding
news.

SPRINT_JULES_TELEGRAM_NEWS_ALERTS.md (v1).
SPRINT_JULES_NEWS_BOT_V2_SCORE_TRANSLATE_MACRO.md (v2: impact score, Turkish
translation, US macro/Fed coverage).
"""

from unittest.mock import MagicMock, patch

from database import UserSettings
from services.news_job_service import _preference_enabled, run_news_alert_cycle


class TestPreferenceEnabled:
    """Real DB layer (not mocked) -- matches tests/test_notification_dispatcher.py's
    pattern for the equivalent trades/health-alert preference gate."""

    def test_defaults_enabled_without_user_settings_row(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr("database.get_session", session_factory)
        assert _preference_enabled("market_news") is True

    def test_respects_explicit_false(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr("database.get_session", session_factory)
        db_session.add(UserSettings(user_id=1, notification_preferences={"market_news": False}))
        db_session.commit()
        assert _preference_enabled("market_news") is False

    def test_missing_key_defaults_true(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr("database.get_session", session_factory)
        db_session.add(UserSettings(user_id=1, notification_preferences={"trade_opened": False}))
        db_session.commit()
        assert _preference_enabled("vc_funding_news") is True


def _fake_news_service(
    headlines: list[str],
    matches: dict[str, list[str]],
    vc: dict[str, list[str]] | None = None,
    scored: dict[str, dict] | None = None,
    macro_headlines: list[str] | None = None,
    is_macro: dict[str, bool] | None = None,
):
    """Build a MagicMock NewsService returning controlled, deterministic data.

    By default: no macro headlines, translate_to_turkish is an identity
    passthrough (so tests can assert on the original English text unless a
    test specifically cares about translation).
    """
    ns = MagicMock()
    ns.fetch_rss_feeds.return_value = [{"title": h, "published": ""} for h in headlines]
    ns.fetch_macro_rss_feeds.return_value = [{"title": h, "published": ""} for h in (macro_headlines or [])]
    ns.is_macro_headline.side_effect = lambda h: (is_macro or {}).get(h, False)
    ns.match_headline_to_symbols.side_effect = lambda h, symbols=None: matches.get(h, [])
    ns.detect_vc_funding.side_effect = lambda h: (vc or {}).get(h, [])
    ns.classify_and_score.return_value = scored or {}
    ns.translate_to_turkish.side_effect = lambda h: h
    return ns


class TestMarketMovingNews:

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_positive_sentiment_alerts_news_bot_with_score_in_turkish(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        news_bot = MagicMock()
        vc_bot = MagicMock()
        mock_mgr_cls.get_instance.side_effect = lambda name: {"news": news_bot, "vc_funding": vc_bot}[name]

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["BTC"]},
            scored={headline.strip().lower(): {"sentiment": "positive", "score": 78}},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_called_once()
        sent_text = news_bot.send_alert_threadsafe.call_args[0][0]
        assert "BTC" in sent_text
        assert "🟢" in sent_text
        assert "POZİTİF" in sent_text
        assert "78/100" in sent_text
        vc_bot.send_alert_threadsafe.assert_not_called()
        mock_record.assert_called_once()
        ns.translate_to_turkish.assert_called_once_with(headline)

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_alert_includes_source_impact_tier_and_reason(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        news_bot = MagicMock()
        vc_bot = MagicMock()
        mock_mgr_cls.get_instance.side_effect = lambda name: {"news": news_bot, "vc_funding": vc_bot}[name]

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = MagicMock()
        ns.fetch_rss_feeds.return_value = [
            {"title": headline, "published": "", "source_name": "CoinDesk"}
        ]
        ns.fetch_macro_rss_feeds.return_value = []
        ns.is_macro_headline.return_value = False
        ns.match_headline_to_symbols.side_effect = lambda h, symbols=None: ["BTC"] if h == headline else []
        ns.detect_vc_funding.return_value = []
        ns.classify_and_score.return_value = {
            headline.strip().lower(): {
                "sentiment": "positive", "score": 82,
                "reason": "Large ETF inflows reduce available exchange supply",
            }
        }
        ns.translate_to_turkish.side_effect = lambda h: h

        run_news_alert_cycle(news_service=ns)

        sent_text = news_bot.send_alert_threadsafe.call_args[0][0]
        assert "Kaynak: CoinDesk" in sent_text
        assert "🔥 YÜKSEK" in sent_text  # score 82 >= 75
        assert "Large ETF inflows reduce available exchange supply" in sent_text
        assert "82/100" in sent_text

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_alert_omits_reason_block_when_fallback_scored(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        news_bot = MagicMock()
        vc_bot = MagicMock()
        mock_mgr_cls.get_instance.side_effect = lambda name: {"news": news_bot, "vc_funding": vc_bot}[name]

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["BTC"]},
            scored={headline.strip().lower(): {"sentiment": "positive", "score": 78, "reason": None}},
        )

        run_news_alert_cycle(news_service=ns)

        sent_text = news_bot.send_alert_threadsafe.call_args[0][0]
        assert "Özet & Etki" not in sent_text
        assert "Kaynak: RSS" in sent_text  # no source_name in the fixture -> falls back to "RSS"

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_neutral_sentiment_does_not_alert(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Ethereum network sees routine upgrade"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["ETH"]},
            scored={headline.strip().lower(): {"sentiment": "neutral", "score": 5}},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_not_called()
        mock_record.assert_not_called()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_low_impact_score_does_not_alert(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        # Regression: the impact score was always computed and shown in the
        # alert text ("Etki: X/100") but never actually gated whether one
        # fired -- a routine, barely-relevant headline sent exactly as
        # readily as genuinely market-moving news. Below
        # NEWS_MIN_IMPACT_SCORE (40 by default), non-neutral is not enough.
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Minor exchange lists a small-cap altcoin"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["BTC"]},
            scored={headline.strip().lower(): {"sentiment": "positive", "score": 25}},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_not_called()
        # Never actually pushed -- must not be marked "sent" either, or a
        # later cycle could never re-evaluate it if it somehow became more
        # relevant.
        mock_record.assert_not_called()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_score_exactly_at_threshold_alerts(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Regulator announces new crypto framework"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["BTC"]},
            scored={headline.strip().lower(): {"sentiment": "positive", "score": 40}},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_called_once()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_headline_matching_no_symbol_is_skipped(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Local weather forecast for the weekend"
        ns = _fake_news_service([headline], matches={headline: []})

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_not_called()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=True)  # already sent
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_already_sent_headline_is_deduped(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["BTC"]},
            scored={headline.strip().lower(): {"sentiment": "positive", "score": 60}},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_not_called()
        mock_record.assert_not_called()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=False)  # muted
    @patch("services.news_job_service.TelegramBotManager")
    def test_preference_disabled_skips_alert(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["BTC"]},
            scored={headline.strip().lower(): {"sentiment": "positive", "score": 60}},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_not_called()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_duplicate_headlines_across_feeds_deduped_within_one_cycle(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        """Same headline appearing in both RSS feeds should only be
        processed (scored, alerted) once per cycle."""
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = MagicMock()
        ns.fetch_rss_feeds.return_value = [
            {"title": headline, "published": ""},
            {"title": headline, "published": ""},  # duplicate, e.g. from the 2nd feed
        ]
        ns.fetch_macro_rss_feeds.return_value = []
        ns.match_headline_to_symbols.return_value = ["BTC"]
        ns.detect_vc_funding.return_value = []
        ns.classify_and_score.return_value = {headline.strip().lower(): {"sentiment": "positive", "score": 60}}
        ns.translate_to_turkish.side_effect = lambda h: h

        run_news_alert_cycle(news_service=ns)

        # classify_and_score called once with the deduplicated unique headline list
        ns.classify_and_score.assert_called_once_with([headline])
        news_bot.send_alert_threadsafe.assert_called_once()


class TestMacroNews:

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_macro_headline_alerts_with_btc_market_wide_label(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Fed holds interest rates steady, signals no near-term cuts"
        ns = _fake_news_service(
            [],
            matches={},
            macro_headlines=[headline],
            is_macro={headline: True},
            scored={headline.strip().lower(): {"sentiment": "negative", "score": 82}},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_called_once()
        sent_text = news_bot.send_alert_threadsafe.call_args[0][0]
        assert "BTC" in sent_text
        assert "🔴" in sent_text
        assert "NEGATİF" in sent_text
        assert "82/100" in sent_text

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_non_macro_entry_from_macro_feed_is_dropped(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        """A headline from the macro RSS feed that doesn't actually match
        MACRO_KEYWORDS (e.g. general MarketWatch top-story noise) must not
        be treated as macro news."""
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Local sports team wins championship"
        ns = _fake_news_service(
            [],
            matches={},
            macro_headlines=[headline],
            is_macro={headline: False},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_not_called()
        ns.classify_and_score.assert_not_called()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_crypto_and_macro_headlines_share_one_scoring_call(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        """Crypto market-moving candidates and macro candidates must be
        batched into the SAME classify_and_score() call, not two separate
        calls."""
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        crypto_headline = "Bitcoin surges past $70k on ETF inflows"
        macro_headline = "Fed signals rate cuts ahead"
        ns = _fake_news_service(
            [crypto_headline],
            matches={crypto_headline: ["BTC"]},
            macro_headlines=[macro_headline],
            is_macro={macro_headline: True},
            scored={
                crypto_headline.strip().lower(): {"sentiment": "positive", "score": 60},
                macro_headline.strip().lower(): {"sentiment": "positive", "score": 70},
            },
        )

        run_news_alert_cycle(news_service=ns)

        ns.classify_and_score.assert_called_once_with([crypto_headline, macro_headline])
        assert news_bot.send_alert_threadsafe.call_count == 2


class TestVcFundingNews:

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_vc_funding_headline_routes_to_vc_bot_not_news_bot(
        self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        news_bot = MagicMock()
        vc_bot = MagicMock()
        mock_mgr_cls.get_instance.side_effect = lambda name: {"news": news_bot, "vc_funding": vc_bot}[name]

        headline = "Some Protocol raises $20M from Binance Labs and a16z"
        ns = _fake_news_service(
            [headline],
            matches={headline: []},  # doesn't need to match a symbol to be a VC alert
            vc={headline: ["binance labs", "a16z"]},
        )

        run_news_alert_cycle(news_service=ns)

        vc_bot.send_alert_threadsafe.assert_called_once()
        sent_text = vc_bot.send_alert_threadsafe.call_args[0][0]
        assert "🏛️" in sent_text
        news_bot.send_alert_threadsafe.assert_not_called()

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_vc_funding_uses_no_llm_call(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        """VC detection is pure keyword matching -- classify_and_score (the
        LLM path) should not even be invoked for a pure-VC headline that
        doesn't match any of the 25 tracked symbols."""
        mock_mgr_cls.get_instance.return_value = MagicMock()

        headline = "Some Protocol raises $20M from Binance Labs"
        ns = _fake_news_service([headline], matches={headline: []}, vc={headline: ["binance labs"]})

        run_news_alert_cycle(news_service=ns)

        # No symbol-matching candidates at all -- classify_and_score (the
        # LLM path) is skipped entirely, not even called with an empty list.
        ns.classify_and_score.assert_not_called()
