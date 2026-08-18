"""Tests for OLLO Headquarters Commander.

Verifies:
  - Mission profiles are defined for all rooms
  - Planner creates correct plans for query/briefing/greet
  - Context builder collects data without errors
  - Personality system prompt is professional
  - Parser extracts structured output from AI text
  - Briefing generator produces structured briefings
  - OLLO service delegates correctly to AIService
  - Commander memory stores and retrieves records
  - Status returns expected fields
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from services.ai import AIService, GenerationResult, HealthStatus
from services.ollo import (
    PROFILES_BY_ROOM,
    BriefingGenerator,
    BriefingRecord,
    CommanderMemory,
    ContextBuilder,
    MissionProfile,
    OLLOBriefing,
    OLLOContext,
    OLLOResponse,
    OLLOService,
    Plan,
    Planner,
    RecommendationRecord,
    get_profile,
    get_system_prompt,
    parse_briefing,
    parse_response,
)
from services.ollo.mission_profile import (
    COMMAND_DECK,
    COUNCIL_CHAMBER,
    MISSION_ARCHIVE,
    PORTFOLIO,
    RISK_OPERATIONS,
    SCANNER,
    WHALE,
)


class MockAIService:
    """Mock AIService that returns predefined responses."""

    def __init__(self):
        self.provider = MagicMock()
        self.provider.__class__.__name__ = "MockProvider"
        self.provider.model = "test-model"
        self.model = "test-model"
        self.last_messages = None

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        return GenerationResult(
            content=f"Generated response to: {prompt[:50]}",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            tokens_in=10,
            tokens_out=20,
            retries=0,
        )

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        self.last_messages = messages
        return GenerationResult(
            content="OLLO response: I have analyzed the available data. The portfolio shows normal operating conditions. No unusual patterns detected.",
            model="test-model",
            provider="test",
            duration_ms=15.0,
            tokens_in=50,
            tokens_out=30,
            retries=0,
        )

    def health(self) -> HealthStatus:
        return HealthStatus(
            connected=True,
            model="test-model",
            latency_ms=5.0,
            provider="test",
        )


class TestMissionProfiles:
    """Mission profiles are correctly defined."""

    def test_all_profiles_present(self):
        assert len(PROFILES_BY_ROOM) == 7

    def test_command_deck_profile(self):
        p = COMMAND_DECK
        assert p.room_id == "command_deck"
        assert p.priority == 1
        assert "portfolio_summary" in p.allowed_context

    def test_scanner_profile(self):
        p = SCANNER
        assert "scanner_signals" in p.allowed_context
        assert "portfolio_summary" not in p.allowed_context

    def test_portfolio_profile(self):
        p = PORTFOLIO
        assert "portfolio_summary" in p.allowed_context
        assert "portfolio_distribution" in p.allowed_context

    def test_get_profile_default(self):
        p = get_profile("unknown_room")
        assert p.room_id == "command_deck"

    def test_get_profile_existing(self):
        p = get_profile("scanner")
        assert p.room_id == "scanner"

    def test_profile_to_dict(self):
        d = COMMAND_DECK.to_dict()
        assert d["room_id"] == "command_deck"
        assert d["display_name"] == "Command Deck"


class TestPlanner:
    """Planner creates correct plans."""

    def setup_method(self):
        self.planner = Planner()

    def test_plan_query_has_correct_type(self):
        plan = self.planner.plan_query("portfolio", "How are we doing?")
        assert plan.prompt_type == "room_query"
        assert plan.mission_profile.room_id == "portfolio"

    def test_plan_query_scanner_only_context(self):
        plan = self.planner.plan_query("scanner", "Show me signals")
        assert "scanner_signals" in plan.context_keys
        assert "portfolio_summary" not in plan.context_keys

    def test_plan_briefing_defaults_to_morning(self):
        plan = self.planner.plan_briefing("command_deck", "invalid")
        assert plan.briefing_kind == "morning"

    def test_plan_briefing_emergency_loads_full_context(self):
        plan = self.planner.plan_briefing("command_deck", "emergency")
        assert "portfolio_summary" in plan.context_keys
        assert "risk_metrics" in plan.context_keys
        assert "market_regime" in plan.context_keys

    def test_plan_greet_minimal_context(self):
        plan = self.planner.plan_greet("command_deck")
        assert "portfolio_summary" in plan.context_keys
        assert "scanner_signals" not in plan.context_keys

    def test_plan_to_dict(self):
        plan = self.planner.plan_query("command_deck", "status?")
        d = plan.to_dict()
        assert d["mission_profile"] == "command_deck"
        assert d["prompt_type"] == "room_query"


class TestContextBuilder:
    """Context builder collects data without errors."""

    def setup_method(self):
        self.builder = ContextBuilder()

    def test_build_empty_keys(self):
        ctx = self.builder.build([], room="test")
        assert isinstance(ctx, OLLOContext)
        assert ctx.room == "test"

    def test_build_unknown_key_logs_error(self):
        ctx = self.builder.build(["nonexistent_key"], room="test")
        assert len(ctx.errors) > 0

    def test_build_known_keys_safely(self):
        ctx = self.builder.build(["portfolio_summary"], room="test")
        assert isinstance(ctx, OLLOContext)

    def test_context_to_dict(self):
        ctx = self.builder.build([], room="test")
        d = ctx.to_dict()
        assert "room" in d

    def test_context_summary_line(self):
        ctx = self.builder.build(["portfolio_summary"], room="test")
        summary = ctx.summary_line()
        assert "portfolio_summary" in summary or "Context loaded:" in summary

    def test_build_multiple_keys(self):
        ctx = self.builder.build(["portfolio_summary", "market_regime"], room="command_deck")
        assert isinstance(ctx.portfolio_summary, dict) or ctx.portfolio_summary is None
        assert isinstance(ctx.market_regime, dict) or ctx.market_regime is None

    def test_load_whale_success_and_failure(self):
        # 1. Success case using mocks
        mock_whale_service = MagicMock()
        mock_whale_service.detect.return_value = [{"type": "WHALE_MOVE", "symbol": "BTC", "severity": "high"}]
        mock_market_service = MagicMock()
        mock_asset = MagicMock()
        mock_asset.is_empty = False
        mock_asset.indicators = {"volume_score": 0.95, "volatility_score": 0.8}
        mock_asset.price = 50000.0
        mock_asset.intelligence = None
        mock_market_service.get_asset.return_value = mock_asset

        with patch("market.intelligence.whale.WhaleService", return_value=mock_whale_service), \
             patch("market.services.MarketDataService", return_value=mock_market_service):
            ctx = self.builder.build(["whale_activity"])
            assert ctx.whale_activity is not None
            assert ctx.whale_activity["status"] == "active"
            assert ctx.whale_activity["signal_count"] == 2  # for both BTC and ETH
            assert len(ctx.whale_activity["signals"]) == 2

        # 2. Failure case
        with patch("market.intelligence.whale.WhaleService", side_effect=Exception("Whale service error")):
            ctx = self.builder.build(["whale_activity"])
            assert ctx.whale_activity is None

    def test_load_news_success_ranks_by_impact_score(self):
        mock_news_service = MagicMock()
        mock_news_service.fetch_rss_feeds.return_value = [
            {"title": "Bitcoin surges past $60k on ETF inflows"},
            {"title": "Minor exchange adds obscure altcoin"},
        ]
        mock_news_service.classify_and_score.return_value = {
            "bitcoin surges past $60k on etf inflows": {"sentiment": "positive", "score": 85},
            "minor exchange adds obscure altcoin": {"sentiment": "neutral", "score": 10},
        }

        with patch("market.intelligence.news.NewsService", return_value=mock_news_service):
            ctx = self.builder.build(["news_headlines"])

        assert ctx.news_headlines["status"] == "active"
        assert len(ctx.news_headlines["headlines"]) == 2
        # Highest-impact headline ranked first.
        assert ctx.news_headlines["headlines"][0]["score"] == 85

    def test_load_news_no_headlines_returns_no_data_status(self):
        mock_news_service = MagicMock()
        mock_news_service.fetch_rss_feeds.return_value = []

        with patch("market.intelligence.news.NewsService", return_value=mock_news_service):
            ctx = self.builder.build(["news_headlines"])

        assert ctx.news_headlines == {"headlines": [], "status": "no_data"}
        mock_news_service.classify_and_score.assert_not_called()

    def test_load_news_failure_returns_none(self):
        with patch("market.intelligence.news.NewsService", side_effect=Exception("News service error")):
            ctx = self.builder.build(["news_headlines"])
        assert ctx.news_headlines is None

    def test_load_scanner_success(self):
        # Regression test: _load_scanner() used to import a nonexistent
        # scanner.core.ScannerEngine, which raised ImportError on every call
        # (silently swallowed, so scanner data was always missing from OLLO
        # briefings). The real class is OpportunityScanner.
        mock_opp = MagicMock()
        mock_opp.symbol = "BTCUSDT"
        mock_opp.side = "LONG"
        mock_opp.score = 0.85
        mock_scanner = MagicMock()
        mock_scanner.scan.return_value = [mock_opp]

        with patch("scanner.core.OpportunityScanner", return_value=mock_scanner):
            ctx = self.builder.build(["scanner_signals"])
            assert ctx.scanner_signals is not None
            assert ctx.scanner_signals["signal_count"] == 1
            assert len(ctx.errors) == 0

    def test_load_risk_success_and_failure(self):
        # 1. Success case using mocks
        from risk.models import RiskCheckDetail, RiskDecision

        checks = [
            RiskCheckDetail(name="MAX_OPEN_TRADES", passed=True, value=2.0, limit=3.0),
            RiskCheckDetail(name="PORTFOLIO_EXPOSURE", passed=True, value=100.0, limit=1000.0),
            RiskCheckDetail(name="DAILY_LOSS_LIMIT", passed=True, value=50.0, limit=500.0),
        ]
        mock_decision = RiskDecision(allowed=True, reason="", checks=tuple(checks))

        mock_risk_manager = MagicMock()
        mock_risk_manager.evaluate_trade.return_value = mock_decision

        with patch("risk_manager.RiskManager", return_value=mock_risk_manager):
            ctx = self.builder.build(["risk_metrics"])
            assert ctx.risk_metrics is not None
            assert ctx.risk_metrics["status"] == "active"
            assert ctx.risk_metrics["open_trades"] == 2
            assert ctx.risk_metrics["portfolio_exposure"] == 100.0
            assert ctx.risk_metrics["daily_loss"] == 50.0

        # 2. Failure case
        with patch("risk_manager.RiskManager", side_effect=Exception("Risk manager error")):
            ctx = self.builder.build(["risk_metrics"])
            assert ctx.risk_metrics is None

    def test_load_risk_exposure_fallback_uses_real_notional(self, db_session, session_factory):
        """When PORTFOLIO_EXPOSURE is absent from decision.checks (e.g. MAX_OPEN_TRADES
        already failed), the exposure fallback must use real notional (quantity * entry
        via PaperTrade), not raw Trade.entry -- same bug already fixed in
        risk_manager.py itself."""
        from database import PaperTrade, Trade
        from risk.models import RiskCheckDetail, RiskDecision

        # High-unit-price BTC trade, but a small real quantity -> small real notional.
        trade = Trade(symbol="BTCUSDT", side="LONG", entry=150000.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()
        paper_trade = PaperTrade(
            position_id=trade.id,
            symbol="BTCUSDT",
            side="LONG",
            entry=150000.0,
            quantity=0.1,
            status="OPEN",
        )
        db_session.add(paper_trade)
        db_session.flush()

        # Only MAX_OPEN_TRADES present -> PORTFOLIO_EXPOSURE missing from checks,
        # matching how the real early short-circuit triggers this fallback.
        mock_decision = RiskDecision(
            allowed=False,
            reason="Maximum open trades reached",
            rejection_code="MAX_OPEN_TRADES",
            checks=(RiskCheckDetail(name="MAX_OPEN_TRADES", passed=False, value=3.0, limit=3.0),),
        )
        mock_risk_manager = MagicMock()
        mock_risk_manager.evaluate_trade.return_value = mock_decision
        mock_risk_manager.session_factory = session_factory

        with patch("risk_manager.RiskManager", return_value=mock_risk_manager):
            ctx = self.builder.build(["risk_metrics"])

        assert ctx.risk_metrics is not None
        # Real notional (0.1 * 150,000 = 15,000), not raw entry price (150,000).
        assert ctx.risk_metrics["portfolio_exposure"] == 15000.0

    def test_load_risk_exposure_fallback_excludes_trade_with_no_matching_paper_trade(
        self, db_session, session_factory
    ):
        """A trade with no matching PaperTrade must be excluded from
        portfolio_exposure (fail closed, don't guess), not counted using its
        raw per-unit entry price -- mirrors risk_manager.py's own check."""
        from database import Trade
        from risk.models import RiskCheckDetail, RiskDecision

        trade = Trade(symbol="BTCUSDT", side="LONG", entry=150000.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()
        # Deliberately no matching PaperTrade row.

        mock_decision = RiskDecision(
            allowed=False,
            reason="Maximum open trades reached",
            rejection_code="MAX_OPEN_TRADES",
            checks=(RiskCheckDetail(name="MAX_OPEN_TRADES", passed=False, value=3.0, limit=3.0),),
        )
        mock_risk_manager = MagicMock()
        mock_risk_manager.evaluate_trade.return_value = mock_decision
        mock_risk_manager.session_factory = session_factory

        with patch("risk_manager.RiskManager", return_value=mock_risk_manager):
            ctx = self.builder.build(["risk_metrics"])

        assert ctx.risk_metrics is not None
        assert ctx.risk_metrics["portfolio_exposure"] == 0.0

    def test_load_risk_daily_loss_fallback_uses_real_dollar_pnl(self, db_session, session_factory):
        """When DAILY_LOSS_LIMIT is absent from decision.checks (e.g. MAX_OPEN_TRADES
        already failed), the daily-loss fallback must use real dollar pnl (quantity *
        pnl via PaperTrade), not raw per-unit Trade.pnl -- same bug already fixed in
        risk_manager.py's own DAILY_LOSS_LIMIT check. A trade with no matching
        PaperTrade must be excluded entirely (fail closed, don't guess), not
        counted using its raw per-unit pnl -- this was itself a bug, fixed
        alongside the identical issue in execution/paper_executor.py."""
        from datetime import UTC, datetime

        from database import PaperTrade, Trade
        from risk.models import RiskCheckDetail, RiskDecision

        today = datetime.now(UTC)

        # Trade A: raw per-unit pnl -2000.0, quantity 2.0 -> real dollar loss -4000.0
        trade_a = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000.0, status="SL_HIT",
            pnl=-2000.0, closed_at=today,
        )
        db_session.add(trade_a)
        db_session.flush()
        db_session.add(PaperTrade(
            position_id=trade_a.id, symbol="BTCUSDT", side="LONG",
            entry=50000.0, quantity=2.0, pnl=-2000.0, status="CLOSED",
        ))

        # Trade B: no matching PaperTrade -> must be excluded, not counted via raw pnl.
        trade_b = Trade(
            symbol="ETHUSDT", side="LONG", entry=3000.0, status="SL_HIT",
            pnl=-500.0, closed_at=today,
        )
        db_session.add(trade_b)
        db_session.flush()

        # Only MAX_OPEN_TRADES present -> DAILY_LOSS_LIMIT missing from checks,
        # matching how the real early short-circuit triggers this fallback.
        mock_decision = RiskDecision(
            allowed=False,
            reason="Maximum open trades reached",
            rejection_code="MAX_OPEN_TRADES",
            checks=(RiskCheckDetail(name="MAX_OPEN_TRADES", passed=False, value=3.0, limit=3.0),),
        )
        mock_risk_manager = MagicMock()
        mock_risk_manager.evaluate_trade.return_value = mock_decision
        mock_risk_manager.session_factory = session_factory

        with patch("risk_manager.RiskManager", return_value=mock_risk_manager):
            ctx = self.builder.build(["risk_metrics"])

        assert ctx.risk_metrics is not None
        # Only Trade A counted (real dollar loss -4000.0); Trade B excluded
        # since it has no matching PaperTrade.
        assert ctx.risk_metrics["daily_loss"] == 4000.0

    def test_load_trade_history_success_and_failure(self):
        # 1. Success case using mock
        mock_tm = MagicMock()
        mock_tm.stats.return_value = {
            "total_entries": 10,
            "wins": 6,
            "losses": 4,
            "win_rate_pct": 60.0,
            "total_pnl": 150.0,
            "top_tags": [{"tag": "breakout", "count": 3}]
        }

        from memory.trade_memory import TradeMemoryEntry
        mock_trades = [
            TradeMemoryEntry(symbol="BTCUSDT", side="BUY", result="WIN", pnl=100.0, lessons=["Stick to plan"]),
            TradeMemoryEntry(symbol="ETHUSDT", side="SELL", result="LOSS", pnl=-50.0, lessons=["Stop loss respected"]),
            TradeMemoryEntry(symbol="SOLUSDT", side="BUY", result="PENDING", pnl=0.0, lessons=[]),
        ]
        mock_tm.list.return_value = mock_trades

        with patch("memory.trade_memory.TradeMemory", return_value=mock_tm):
            ctx = self.builder.build(["trade_history"])
            assert ctx.trade_history is not None
            assert ctx.trade_history["stats"]["win_rate_pct"] == 60.0
            assert len(ctx.trade_history["recent_closed_trades"]) == 2
            assert ctx.trade_history["recent_closed_trades"][0]["symbol"] == "BTCUSDT"
            assert ctx.trade_history["recent_closed_trades"][1]["result"] == "LOSS"

        # 2. Failure case
        with patch("memory.trade_memory.TradeMemory", side_effect=Exception("Database error")):
            ctx = self.builder.build(["trade_history"])
            assert ctx.trade_history is None

    def test_load_recent_conversation_success_and_failure(self):
        # 1. Success case using mock
        mock_mem = MagicMock()
        mock_mem.recent_recommendations.return_value = [
            RecommendationRecord(query="Hello", room="command_deck", response_text="Hi back " * 50, timestamp="2026-08-01")
        ]
        mock_mem.last_briefing.return_value = BriefingRecord(kind="morning", text="Briefing text " * 50, timestamp="2026-08-01")

        with patch("services.ollo.memory.CommanderMemory", return_value=mock_mem):
            ctx = self.builder.build(["recent_conversation"], room="command_deck")
            assert ctx.recent_conversation is not None
            exchanges = ctx.recent_conversation["recent_exchanges"]
            assert len(exchanges) == 1
            assert len(exchanges[0]["response_text"]) == 203  # 200 + '...'
            assert exchanges[0]["response_text"].endswith("...")

            briefing = ctx.recent_conversation["last_briefing"]
            assert briefing is not None
            assert briefing["kind"] == "morning"
            assert len(briefing["text"]) == 203  # 200 + '...'
            assert briefing["text"].endswith("...")

        # 2. Failure case
        with patch("services.ollo.memory.CommanderMemory", side_effect=Exception("Database down")):
            ctx = self.builder.build(["recent_conversation"], room="command_deck")
            assert ctx.recent_conversation is None


class TestPersonality:
    """Personality system prompt is professional."""

    def test_system_prompt_exists(self):
        prompt = get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_system_prompt_is_professional(self):
        prompt = get_system_prompt()
        assert "OLLO" in prompt
        assert "Chief Investment Officer" in prompt
        assert "NEVER" in prompt

    def test_system_prompt_no_gimmicks(self):
        prompt = get_system_prompt()
        assert "!" not in prompt or "Never" in prompt

    def test_system_prompt_default_language_has_no_directive(self):
        # Regression: OLLO's real AI responses (not just the error fallback
        # -- see i18n_fallback.py) ignored the UI's selected language
        # entirely, always answering in English regardless of the Turkish
        # toggle, because nothing in the prompt ever told the model which
        # language to respond in.
        assert "Turkish" not in get_system_prompt()
        assert "Turkish" not in get_system_prompt("en")

    def test_system_prompt_turkish_adds_directive(self):
        prompt = get_system_prompt("tr")
        assert "Turkish" in prompt
        # Directive must be additive, not a replacement of the real prompt.
        assert "OLLO" in prompt
        assert "Chief Investment Officer" in prompt


class TestParser:
    """Parser extracts structured output from AI text."""

    def test_parse_response_basic(self):
        r = parse_response("Simple response", room="command_deck")
        assert isinstance(r, OLLOResponse)
        assert r.text == "Simple response"
        assert r.room == "command_deck"

    def test_parse_response_with_metadata(self):
        r = parse_response("Test", provider="nvidia", model="llama", duration_ms=100.0, tokens_in=10, tokens_out=20)
        assert r.provider == "nvidia"
        assert r.model == "llama"
        assert r.duration_ms == 100.0
        assert r.tokens_in == 10
        assert r.tokens_out == 20

    def test_parse_response_to_dict(self):
        r = parse_response("Hello", room="deck")
        d = r.to_dict()
        assert d["text"] == "Hello"
        assert d["room"] == "deck"
        assert "timestamp" in d
        assert "tokens" in d

    def test_parse_briefing(self):
        b = parse_briefing("morning", "Good morning briefing text")
        assert isinstance(b, OLLOBriefing)
        assert b.kind == "morning"
        assert b.title == "Morning Briefing"

    def test_parse_briefing_to_dict(self):
        b = parse_briefing("evening", "Evening text", provider="nvidia")
        d = b.to_dict()
        assert d["kind"] == "evening"
        assert d["provider"] == "nvidia"

    def test_parse_response_extracts_sections(self):
        text = "# Overview\n- Point one\n- Point two\n# Details\n- Detail one"
        r = parse_response(text)
        assert len(r.sections) > 0


class TestBriefingGenerator:
    """Briefing generator produces structured briefings."""

    def test_generate_returns_briefing(self):
        mock_ai = MockAIService()
        gen = BriefingGenerator(mock_ai)
        plan = Plan(
            mission_profile=COMMAND_DECK,
            context_keys=["portfolio_summary"],
            prompt_type="briefing",
            prompt_template="briefing/morning",
            briefing_kind="morning",
        )
        ctx = OLLOContext(room="command_deck", portfolio_summary={"open_trades": 3, "total_pnl": 500})
        briefing = gen.generate(plan, ctx)
        assert isinstance(briefing, OLLOBriefing)
        assert briefing.text.startswith("OLLO response")


class TestOLLOService:
    """OLLO service delegates correctly to AIService."""

    def setup_method(self):
        self.mock_ai = MockAIService()

        # CommanderMemory(session_factory=database.get_session) is
        # OLLOService's default -- meaning without this, every test in this
        # class was writing real CommanderMemoryEntry rows into the actual
        # live production database (elite_trial.db, per .env's
        # DATABASE_URL), not a test-isolated one. Found live 2026-08-18:
        # the real db had 978 fake "Test query"/"How is the portfolio?"
        # entries plus real HTTP-429 failure messages accumulated from past
        # test runs. Same isolated-in-memory-SQLite pattern as
        # conftest.py's _default_engine(), just built directly here since
        # this class predates pytest-fixture-style setup.
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from database import Base
        test_engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        Base.metadata.create_all(test_engine)
        self._test_session_factory = sessionmaker(bind=test_engine)
        test_memory = CommanderMemory(session_factory=self._test_session_factory)

        self.svc = OLLOService(ai_service=self.mock_ai, memory=test_memory)

        # Command Deck's context now includes news_headlines (see
        # services/ollo/context.py::_load_news()) -- without this, query()/
        # briefing() below silently hit the real RSS feeds and, if any
        # headlines came back, the real NVIDIA API via
        # NewsService.classify_and_score(), even though ai_service above is
        # mocked (that mock only covers OLLO's own chat generation, not
        # context-gathering). An empty RSS result makes _load_news() return
        # early before ever calling classify_and_score() -- see that
        # method's early "if not headlines: return" -- so this one patch
        # blocks both the real RSS call and the real NVIDIA call.
        self._fetch_rss_patcher = patch(
            "market.intelligence.news.NewsService.fetch_rss_feeds", return_value=[]
        )
        self._fetch_rss_patcher.start()

    def teardown_method(self):
        self._fetch_rss_patcher.stop()

    def test_greet_returns_response(self):
        r = self.svc.greet("command_deck")
        assert isinstance(r, OLLOResponse)
        assert r.text.startswith("OLLO response")

    def test_query_returns_response(self):
        r = self.svc.query("How is the portfolio?", "portfolio")
        assert isinstance(r, OLLOResponse)
        assert r.room == "portfolio"

    def test_briefing_returns_briefing(self):
        b = self.svc.briefing("morning", "command_deck")
        assert isinstance(b, OLLOBriefing)
        assert b.kind == "morning"

    def test_status_returns_dict(self):
        s = self.svc.status()
        assert "provider" in s
        assert "model" in s
        assert "current_mission_profile" in s
        assert "ai_health" in s
        assert "memory" in s

    def test_status_health_connected(self):
        s = self.svc.status()
        assert s["ai_health"]["connected"] is True

    def test_query_records_in_memory(self):
        self.svc.query("Test query", "command_deck")
        recs = self.svc.memory.recent_recommendations()
        assert len(recs) == 1
        assert recs[0].query == "Test query"

    def test_briefing_records_in_memory(self):
        self.svc.briefing("morning", "command_deck")
        briefings = self.svc.memory.recent_briefings()
        assert len(briefings) == 1
        assert briefings[0].kind == "morning"

    def test_greet_no_memory_record(self):
        mem_before = len(self.svc.memory.recent_recommendations())
        self.svc.greet("command_deck")
        mem_after = len(self.svc.memory.recent_recommendations())
        assert mem_after == mem_before

    def test_ai_service_property(self):
        assert self.svc.ai_service is self.mock_ai

    def test_greet_surfaces_honest_message_when_ai_provider_fails(self):
        # Same bug class as query()/briefing() below, found by a fresh audit
        # after those two were fixed -- greet() had the identical gap.
        failing_ai = MockAIService()
        failing_ai.chat = MagicMock(return_value=GenerationResult(
            content="",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            retries=3,
            error="HTTP 429",
        ))
        svc = OLLOService(ai_service=failing_ai)

        r = svc.greet("command_deck")

        assert r.text != ""
        assert "429" in r.text

    def test_query_surfaces_honest_message_when_ai_provider_fails(self):
        # Regression: GenerationResult.content is "" when the AI provider
        # exhausts its retries (e.g. rate-limited) -- the request still
        # succeeds at the HTTP layer, so without this check the founder saw
        # a silent, blank response with no indication anything went wrong.
        failing_ai = MockAIService()
        failing_ai.chat = MagicMock(return_value=GenerationResult(
            content="",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            retries=3,
            error="HTTP 429",
        ))
        svc = OLLOService(ai_service=failing_ai)

        r = svc.query("How is the portfolio?", "command_deck")

        assert r.text != ""
        assert "429" in r.text

    def test_briefing_surfaces_honest_message_when_ai_provider_fails(self):
        failing_ai = MockAIService()
        failing_ai.chat = MagicMock(return_value=GenerationResult(
            content="",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            retries=3,
            error="HTTP 429",
        ))
        svc = OLLOService(ai_service=failing_ai)

        b = svc.briefing("morning", "command_deck")

        assert b.text != ""
        assert "429" in b.text

    def test_greet_fallback_respects_language_param(self):
        # Regression: the AI-unavailable fallback text was hardcoded English
        # regardless of the UI's selected language -- greet()/query()/
        # briefing() now thread a language param through to
        # services/ollo/i18n_fallback.py's small en/tr dict.
        failing_ai = MockAIService()
        failing_ai.chat = MagicMock(return_value=GenerationResult(
            content="",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            retries=3,
            error="HTTP 429",
        ))
        svc = OLLOService(ai_service=failing_ai)

        r = svc.greet("command_deck", language="tr")

        assert "429" in r.text
        assert "Kurucu" in r.text

    def test_query_fallback_respects_language_param(self):
        failing_ai = MockAIService()
        failing_ai.chat = MagicMock(return_value=GenerationResult(
            content="",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            retries=3,
            error="HTTP 429",
        ))
        svc = OLLOService(ai_service=failing_ai)

        r = svc.query("Portföy nasıl?", "command_deck", language="tr")

        assert "429" in r.text
        assert "Kurucu" in r.text

    def test_query_with_turkish_language_sends_turkish_directive_to_the_model(self):
        # The real bug (not just the error-fallback case above): OLLO's
        # actual successful AI responses ignored the UI's selected language
        # entirely, since nothing in the system prompt ever told the model
        # to answer in Turkish -- confirmed live (a real Turkish-UI session
        # got an English reply). Assert the directive actually reaches the
        # model's system message, not just that a fallback string exists.
        svc = OLLOService(ai_service=self.mock_ai)
        svc.query("Portföy nasıl?", "command_deck", language="tr")
        system_message = self.mock_ai.last_messages[0]["content"]
        assert "Turkish" in system_message

    def test_greet_with_turkish_language_sends_turkish_directive_to_the_model(self):
        svc = OLLOService(ai_service=self.mock_ai)
        svc.greet("command_deck", language="tr")
        system_message = self.mock_ai.last_messages[0]["content"]
        assert "Turkish" in system_message

    def test_query_default_language_sends_no_turkish_directive(self):
        svc = OLLOService(ai_service=self.mock_ai)
        svc.query("How is the portfolio?", "command_deck")
        system_message = self.mock_ai.last_messages[0]["content"]
        assert "Turkish" not in system_message

    def test_briefing_fallback_respects_language_param(self):
        failing_ai = MockAIService()
        failing_ai.chat = MagicMock(return_value=GenerationResult(
            content="",
            model="test-model",
            provider="test",
            duration_ms=10.0,
            retries=3,
            error="HTTP 429",
        ))
        svc = OLLOService(ai_service=failing_ai)

        b = svc.briefing("morning", "command_deck", language="tr")

        assert "429" in b.text
        assert "Kurucu" in b.text


class TestCommanderMemory:
    """Commander memory stores and retrieves records."""

    def test_initial_state(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        s = mem.status()
        assert s["briefings_stored"] == 0
        assert s["recommendations_stored"] == 0

    def test_record_and_retrieve_briefing(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        mem.record_briefing("morning", "Briefing text")
        briefings = mem.recent_briefings()
        assert len(briefings) == 1
        assert briefings[0].kind == "morning"

    def test_last_briefing(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        mem.record_briefing("morning", "Morning text")
        mem.record_briefing("evening", "Evening text")
        assert mem.last_briefing().kind == "evening"
        assert mem.last_briefing("morning").text == "Morning text"

    def test_last_briefing_empty(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        assert mem.last_briefing() is None

    def test_record_and_retrieve_recommendation(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        mem.record_recommendation("Query text", "command_deck", "Response text")
        recs = mem.recent_recommendations()
        assert len(recs) == 1
        assert recs[0].query == "Query text"
        assert recs[0].room == "command_deck"

    def test_preferences(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        mem.set_preference("briefing_style", "concise")
        assert mem.get_preference("briefing_style") == "concise"
        assert mem.get_preference("nonexistent") is None

    def test_recent_recommendations_limit(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        for i in range(10):
            mem.record_recommendation(f"Q{i}", "room", f"R{i}")
        assert len(mem.recent_recommendations(limit=3)) == 3

    def test_recent_recommendations_room_filtering(self, session_factory):
        mem = CommanderMemory(session_factory=session_factory)
        mem.record_recommendation("Q1", "command_deck", "R1")
        mem.record_recommendation("Q2", "scanner", "R2")
        mem.record_recommendation("Q3", "command_deck", "R3")

        # room filtering works
        deck_recs = mem.recent_recommendations(room="command_deck")
        assert len(deck_recs) == 2
        assert deck_recs[0].query == "Q1"
        assert deck_recs[1].query == "Q3"

        scanner_recs = mem.recent_recommendations(room="scanner")
        assert len(scanner_recs) == 1
        assert scanner_recs[0].query == "Q2"

        # no argument retrieves all
        all_recs = mem.recent_recommendations()
        assert len(all_recs) == 3

    def test_cross_instance_persistence(self, session_factory):
        mem1 = CommanderMemory(session_factory=session_factory)
        mem1.record_briefing("morning", "Briefing from instance 1")

        mem2 = CommanderMemory(session_factory=session_factory)
        briefings = mem2.recent_briefings()
        assert len(briefings) == 1
        assert briefings[0].text == "Briefing from instance 1"

    def test_briefing_record_dataclass(self):
        r = BriefingRecord(kind="morning", text="Brief")
        assert r.kind == "morning"

    def test_recommendation_record_dataclass(self):
        r = RecommendationRecord(query="Q", room="R", response_text="Resp")
        assert r.query == "Q"


class TestMissionProfileData:
    """Mission profile data consistency."""

    def test_all_profiles_have_required_fields(self):
        for room_id, p in PROFILES_BY_ROOM.items():
            assert p.room_id == room_id
            assert p.display_name
            assert p.purpose
            assert p.tone in ("strategic", "analytical", "advisory", "cautionary", "reflective", "deliberative")
            assert 1 <= p.priority <= 5
            assert isinstance(p.allowed_context, list)
            assert isinstance(p.allowed_tools, list)

    def test_no_duplicate_room_ids(self):
        assert len(PROFILES_BY_ROOM) == len(set(p.room_id for p in PROFILES_BY_ROOM.values()))

    def test_tone_is_professional(self):
        for p in PROFILES_BY_ROOM.values():
            assert p.tone not in ("excited", "fun", "casual")


class TestOLLOResponseDTO:
    """OLLOResponse DTO correctness."""

    def test_to_dict_contains_all_keys(self):
        r = OLLOResponse(text="Hello", room="deck", provider="nvidia", model="llama", duration_ms=100.0)
        d = r.to_dict()
        assert d["text"] == "Hello"
        assert d["room"] == "deck"
        assert d["provider"] == "nvidia"
        assert d["model"] == "llama"
        assert d["duration_ms"] == 100.0
        assert "timestamp" in d
        assert "sections" in d
