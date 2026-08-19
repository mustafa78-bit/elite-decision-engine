"""Tests for council/fundamental_gate.py -- the veto bridge between
council's News/Whale/Macro agents and the REAL execution path
(execution/pipeline.py). See its module docstring: majority (2/3) quorum,
fails open on any error/missing data, never adds score, only vetoes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from council.base import DIRECTION_BEARISH, DIRECTION_BULLISH, DIRECTION_NEUTRAL, AgentReport
from council.fundamental_gate import check_fundamental_veto


def _report(agent_name: str, direction: str, confidence: float) -> AgentReport:
    return AgentReport(
        agent_name=agent_name, symbol="BTCUSDT", direction=direction,
        confidence=confidence, score=confidence, reasoning=[f"{agent_name} says {direction}"],
    )


def _mock_asset_with_bundle():
    asset = MagicMock()
    asset.intelligence = MagicMock()  # non-None -- presence is all check_fundamental_veto needs
    return asset


class TestCheckFundamentalVeto:

    def test_no_veto_when_no_intelligence_data(self):
        # Fails open: missing data must never itself cause a veto.
        asset = MagicMock()
        asset.intelligence = None
        mds = MagicMock()
        mds.get_asset.return_value = asset

        with patch("market.services.MarketDataService", return_value=mds):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False
        assert result.reason is None

    def test_no_veto_when_all_agents_agree(self):
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BULLISH, 0.8)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BULLISH, 0.8)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False

    def test_no_veto_when_only_one_agent_contradicts(self):
        # Below quorum (needs 2/3) -- a single dissenting agent must not block a trade.
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BEARISH, 0.9)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BULLISH, 0.8)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False

    def test_no_veto_when_contradiction_confidence_too_low(self):
        # 2 agents disagree, but below the confidence threshold -- weak signal, no veto.
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BEARISH, 0.4)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BEARISH, 0.5)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False

    def test_vetoes_when_two_agents_strongly_contradict(self):
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BEARISH, 0.9)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BEARISH, 0.75)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is True
        assert "News" in result.reason
        assert "Whale" in result.reason
        assert "BTCUSDT" in result.reason

    def test_vetoes_when_all_three_agents_strongly_contradict(self):
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BEARISH, 0.9)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BEARISH, 0.8)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_BEARISH, 0.7)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is True

    def test_fails_open_on_exception(self):
        with patch("market.services.MarketDataService", side_effect=Exception("boom")):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False
        assert result.reason is None

    def test_vetoes_on_moderate_confidence_below_old_060_threshold(self):
        # Regression for the 2026-08-19 threshold change (0.60 -> 0.45):
        # confidence here (0.5) would NOT have crossed the old bar at all,
        # so this exact scenario used to be a guaranteed no-veto. 2 agents
        # at 0.5 > the new 0.45 threshold must now veto.
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BEARISH, 0.5)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BEARISH, 0.5)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is True

    def test_no_veto_below_new_045_threshold(self):
        # Still below the new, lower bar -- must not count toward a veto.
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BEARISH, 0.4)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BEARISH, 0.4)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False

    def test_whale_alone_vetoes_via_emergency_override(self):
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BULLISH, 0.5)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BEARISH, 0.9)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is True
        assert "Emergency override" in result.reason
        assert "Whale" in result.reason

    def test_macro_alone_vetoes_via_emergency_override(self):
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_NEUTRAL, 0.5)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BULLISH, 0.5)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_BEARISH, 0.9)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is True
        assert "Emergency override" in result.reason
        assert "Macro" in result.reason

    def test_news_alone_does_not_trigger_emergency_override(self):
        # News is deliberately excluded from the single-agent override --
        # it's LLM-derived sentiment, noisier than Whale/Macro's inputs.
        # Below quorum (only 1 of 3 contradicts) so this must not veto at
        # all, even though News's confidence exceeds the emergency bar.
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BEARISH, 0.95)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BULLISH, 0.5)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False

    def test_emergency_override_requires_extreme_not_just_strong_confidence(self):
        # Whale contradicts strongly (0.75, above the quorum threshold) but
        # not EXTREMELY (below 0.85) -- must not trigger the emergency path,
        # and with only 1 of 3 agents contradicting, must not veto at all.
        mds = MagicMock()
        mds.get_asset.return_value = _mock_asset_with_bundle()

        with patch("market.services.MarketDataService", return_value=mds), \
             patch("council.news_agent.NewsAgent.evaluate", return_value=_report("News", DIRECTION_BULLISH, 0.5)), \
             patch("council.whale_agent.WhaleAgent.evaluate", return_value=_report("Whale", DIRECTION_BEARISH, 0.75)), \
             patch("council.macro_agent.MacroAgent.evaluate", return_value=_report("Macro", DIRECTION_NEUTRAL, 0.5)):
            result = check_fundamental_veto("BTCUSDT", "LONG")

        assert result.vetoed is False
