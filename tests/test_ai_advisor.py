"""Tests for council/ai_advisor.py -- optional, opt-in AI sanity-check
commentary on an already-computed council consensus. See its module
docstring: this must never fail loudly (a broken/unavailable AI call
degrades to None, not an exception) and must never be able to influence
the report it's attached to."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from council.ai_advisor import get_ai_opinion
from council.base import DIRECTION_BULLISH, AgentReport
from council.consensus import CouncilReport


def _report() -> CouncilReport:
    return CouncilReport(
        symbol="BTCUSDT",
        side="LONG",
        consensus_direction=DIRECTION_BULLISH,
        consensus_score=0.82,
        agreement_level="strong",
        agent_reports=[
            AgentReport(
                agent_name="Technical", symbol="BTCUSDT", direction=DIRECTION_BULLISH,
                confidence=0.9, score=0.8, reasoning=["Strong uptrend"],
            ),
        ],
    )


class TestGetAIOpinion:

    def test_returns_content_on_success(self):
        mock_result = MagicMock(content="Looks sound, no red flags.", error=None)
        mock_provider = MagicMock()
        mock_provider.generate.return_value = mock_result

        with patch("services.ai.provider_factory.get_shared_provider", return_value=mock_provider):
            opinion = get_ai_opinion(_report())

        assert opinion == "Looks sound, no red flags."
        mock_provider.generate.assert_called_once()

    def test_returns_none_on_provider_error(self):
        mock_result = MagicMock(content="", error="HTTP 429")
        mock_provider = MagicMock()
        mock_provider.generate.return_value = mock_result

        with patch("services.ai.provider_factory.get_shared_provider", return_value=mock_provider):
            opinion = get_ai_opinion(_report())

        assert opinion is None

    def test_returns_none_on_unexpected_exception(self):
        with patch("services.ai.provider_factory.get_shared_provider", side_effect=Exception("boom")):
            opinion = get_ai_opinion(_report())
        assert opinion is None

    def test_prompt_includes_symbol_and_consensus(self):
        mock_result = MagicMock(content="ok", error=None)
        mock_provider = MagicMock()
        mock_provider.generate.return_value = mock_result

        with patch("services.ai.provider_factory.get_shared_provider", return_value=mock_provider):
            get_ai_opinion(_report())

        prompt = mock_provider.generate.call_args[0][0]
        assert "BTCUSDT" in prompt
        assert DIRECTION_BULLISH in prompt
