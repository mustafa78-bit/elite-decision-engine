"""Tests for services/listings_service.py -- proactive Telegram alerts for
new Binance spot listings."""

from unittest.mock import MagicMock, patch

import requests

from services.listings_service import fetch_binance_new_listings, run_listings_alert_cycle


def _binance_response(articles: list[dict]) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "data": {"catalogs": [{"catalogId": 48, "catalogName": "New Cryptocurrency Listing", "articles": articles}]},
    }
    return resp


class TestFetchBinanceNewListings:

    def test_extracts_genuine_new_listing_and_ignores_noise(self):
        # Real shape confirmed live 2026-08-17: this catalog mixes futures
        # launches and bStocks collateral/trading-pair additions in with
        # genuine new spot listings under the same catalogId.
        articles = [
            {"id": 1, "title": "Binance Futures Will Launch USDⓈ-Margined DOSUSDT Perpetual Contract (2026-08-11)"},
            {"id": 2, "title": "Binance Will Add 1 bStocks Tokenized Securities as Collateral Asset - 2026-08-12"},
            {"id": 3, "title": "Binance Exchange Adds 1 bStocks Trading Pair on Binance Spot - 2026-08-12"},
            {"id": 4, "title": "Binance Will List Aerodrome (AERO) with Seed Tag Applied"},
        ]
        with patch("services.listings_service.requests.get", return_value=_binance_response(articles)):
            listings = fetch_binance_new_listings()

        assert len(listings) == 1
        assert listings[0]["id"] == "4"
        assert listings[0]["tickers"] == ["AERO"]

    def test_extracts_multiple_tickers_from_one_title(self):
        articles = [
            {"id": 5, "title": "Binance Will List Alpha Token (ALPHA) and Beta Coin (BETA)"},
        ]
        with patch("services.listings_service.requests.get", return_value=_binance_response(articles)):
            listings = fetch_binance_new_listings()

        assert listings[0]["tickers"] == ["ALPHA", "BETA"]

    def test_will_list_title_without_a_parenthesized_ticker_is_skipped(self):
        articles = [{"id": 6, "title": "Binance Will List New Assets Soon"}]
        with patch("services.listings_service.requests.get", return_value=_binance_response(articles)):
            listings = fetch_binance_new_listings()
        assert listings == []

    def test_fetch_failure_returns_empty_list(self):
        with patch("services.listings_service.requests.get", side_effect=requests.RequestException("boom")):
            listings = fetch_binance_new_listings()
        assert listings == []

    def test_malformed_response_returns_empty_list(self):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"data": {}}
        with patch("services.listings_service.requests.get", return_value=resp):
            listings = fetch_binance_new_listings()
        assert listings == []


class TestRunListingsAlertCycle:

    @patch("services.listings_service.record_sent_alert")
    @patch("services.listings_service.is_alert_sent", return_value=False)
    @patch("services.listings_service._preference_enabled", return_value=True)
    @patch("services.listings_service.TelegramBotManager")
    @patch("services.listings_service.fetch_binance_new_listings")
    def test_sends_alert_for_new_listing(
        self, mock_fetch, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        vc_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = vc_bot
        mock_fetch.return_value = [
            {"id": "4", "title": "Binance Will List Aerodrome (AERO) with Seed Tag Applied", "tickers": ["AERO"]},
        ]
        ns = MagicMock()
        ns.translate_to_turkish.side_effect = lambda h: h

        run_listings_alert_cycle(news_service=ns)

        # Routes through the existing "vc_funding" bot, not a separate one --
        # at the user's request.
        mock_mgr_cls.get_instance.assert_called_once_with("vc_funding")
        vc_bot.send_alert_threadsafe.assert_called_once()
        sent_text = vc_bot.send_alert_threadsafe.call_args[0][0]
        assert "AERO" in sent_text
        mock_record.assert_called_once_with("new_listing", "4")

    @patch("services.listings_service.record_sent_alert")
    @patch("services.listings_service.is_alert_sent", return_value=True)
    @patch("services.listings_service._preference_enabled", return_value=True)
    @patch("services.listings_service.TelegramBotManager")
    @patch("services.listings_service.fetch_binance_new_listings")
    def test_already_sent_listing_is_deduped(
        self, mock_fetch, mock_mgr_cls, mock_pref, mock_is_sent, mock_record,
    ):
        vc_bot = MagicMock()
        mock_mgr_cls.get_instance.return_value = vc_bot
        mock_fetch.return_value = [{"id": "4", "title": "Binance Will List Aerodrome (AERO)", "tickers": ["AERO"]}]

        run_listings_alert_cycle(news_service=MagicMock())

        vc_bot.send_alert_threadsafe.assert_not_called()
        mock_record.assert_not_called()

    @patch("services.listings_service.fetch_binance_new_listings")
    @patch("services.listings_service._preference_enabled", return_value=False)
    def test_preference_disabled_skips_the_fetch_entirely(self, mock_pref, mock_fetch):
        run_listings_alert_cycle(news_service=MagicMock())
        mock_fetch.assert_not_called()

    @patch("services.listings_service.TelegramBotManager")
    @patch("services.listings_service._preference_enabled", return_value=True)
    @patch("services.listings_service.fetch_binance_new_listings", return_value=[])
    def test_no_listings_does_nothing(self, mock_fetch, mock_pref, mock_mgr_cls):
        run_listings_alert_cycle(news_service=MagicMock())
        mock_mgr_cls.get_instance.assert_not_called()
