"""Tests for services/news_job_service.py -- proactive Telegram alerts for
market-moving crypto news and VC/institutional funding news.

SPRINT_JULES_TELEGRAM_NEWS_ALERTS.md.
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
    sentiment: dict[str, str] | None = None,
):
    """Build a MagicMock NewsService returning controlled, deterministic data."""
    ns = MagicMock()
    ns.fetch_rss_feeds.return_value = [{"title": h, "published": ""} for h in headlines]
    ns.match_headline_to_symbols.side_effect = lambda h, symbols=None: matches.get(h, [])
    ns.detect_vc_funding.side_effect = lambda h: (vc or {}).get(h, [])
    ns.classify_sentiment.return_value = sentiment or {}
    return ns


class TestMarketMovingNews:

    @patch("services.news_job_service.record_sent_alert")
    @patch("services.news_job_service.is_alert_sent", return_value=False)
    @patch("services.news_job_service._preference_enabled", return_value=True)
    @patch("services.news_job_service.TelegramBotManager")
    def test_positive_sentiment_alerts_news_bot(self, mock_mgr_cls, mock_pref, mock_is_sent, mock_record):
        news_bot = MagicMock()
        vc_bot = MagicMock()
        mock_mgr_cls.get_instance.side_effect = lambda name: {"news": news_bot, "vc_funding": vc_bot}[name]

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = _fake_news_service(
            [headline],
            matches={headline: ["BTC"]},
            sentiment={headline.strip().lower(): "positive"},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_called_once()
        sent_text = news_bot.send_alert_threadsafe.call_args[0][0]
        assert "BTC" in sent_text
        assert "🟢" in sent_text
        vc_bot.send_alert_threadsafe.assert_not_called()
        mock_record.assert_called_once()

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
            sentiment={headline.strip().lower(): "neutral"},
        )

        run_news_alert_cycle(news_service=ns)

        news_bot.send_alert_threadsafe.assert_not_called()
        mock_record.assert_not_called()

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
            sentiment={headline.strip().lower(): "positive"},
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
            sentiment={headline.strip().lower(): "positive"},
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
        processed (sentiment-classified, alerted) once per cycle."""
        news_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = news_bot

        headline = "Bitcoin surges past $70k on ETF inflows"
        ns = MagicMock()
        ns.fetch_rss_feeds.return_value = [
            {"title": headline, "published": ""},
            {"title": headline, "published": ""},  # duplicate, e.g. from the 2nd feed
        ]
        ns.match_headline_to_symbols.return_value = ["BTC"]
        ns.detect_vc_funding.return_value = []
        ns.classify_sentiment.return_value = {headline.strip().lower(): "positive"}

        run_news_alert_cycle(news_service=ns)

        # classify_sentiment called once with the deduplicated unique headline list
        ns.classify_sentiment.assert_called_once_with([headline])
        news_bot.send_alert_threadsafe.assert_called_once()


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
        """VC detection is pure keyword matching -- classify_sentiment (the
        LLM path) should not even be invoked for a pure-VC headline that
        doesn't match any of the 25 tracked symbols."""
        mock_mgr_cls.get_instance.return_value = MagicMock()

        headline = "Some Protocol raises $20M from Binance Labs"
        ns = _fake_news_service([headline], matches={headline: []}, vc={headline: ["binance labs"]})

        run_news_alert_cycle(news_service=ns)

        # No symbol-matching candidates at all -- classify_sentiment (the
        # LLM path) is skipped entirely, not even called with an empty list.
        ns.classify_sentiment.assert_not_called()
