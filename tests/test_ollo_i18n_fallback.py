"""Tests for services/ollo/i18n_fallback.py."""

from services.ollo.i18n_fallback import ai_unavailable_message, briefing_unavailable_message


class TestAiUnavailableMessage:

    def test_default_language_is_english(self):
        msg = ai_unavailable_message("HTTP 429")
        assert "HTTP 429" in msg
        assert "Founder" in msg

    def test_turkish(self):
        msg = ai_unavailable_message("HTTP 429", "tr")
        assert "HTTP 429" in msg
        assert "Kurucu" in msg

    def test_unknown_language_falls_back_to_english(self):
        msg = ai_unavailable_message("HTTP 429", "fr")
        assert "Founder" in msg


class TestBriefingUnavailableMessage:

    def test_default_language_is_english(self):
        msg = briefing_unavailable_message("HTTP 503")
        assert "HTTP 503" in msg
        assert "Founder" in msg

    def test_turkish(self):
        msg = briefing_unavailable_message("HTTP 503", "tr")
        assert "HTTP 503" in msg
        assert "Kurucu" in msg

    def test_unknown_language_falls_back_to_english(self):
        msg = briefing_unavailable_message("HTTP 503", "fr")
        assert "Founder" in msg
