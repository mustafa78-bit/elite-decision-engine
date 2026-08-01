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
from unittest.mock import MagicMock

import pytest

from services.ai import AIService, GenerationResult, HealthStatus
from services.ollo import (
    OLLOService,
    Planner,
    Plan,
    ContextBuilder,
    OLLOContext,
    get_system_prompt,
    BriefingGenerator,
    MissionProfile,
    get_profile,
    PROFILES_BY_ROOM,
    OLLOResponse,
    OLLOBriefing,
    parse_response,
    parse_briefing,
    CommanderMemory,
    BriefingRecord,
    RecommendationRecord,
)
from services.ollo.mission_profile import COMMAND_DECK, SCANNER, WHALE, PORTFOLIO, RISK_OPERATIONS, MISSION_ARCHIVE, COUNCIL_CHAMBER


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
        self.svc = OLLOService(ai_service=self.mock_ai)

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


class TestCommanderMemory:
    """Commander memory stores and retrieves records."""

    def setup_method(self):
        self.mem = CommanderMemory()

    def test_initial_state(self):
        s = self.mem.status()
        assert s["briefings_stored"] == 0
        assert s["recommendations_stored"] == 0

    def test_record_and_retrieve_briefing(self):
        self.mem.record_briefing("morning", "Briefing text")
        briefings = self.mem.recent_briefings()
        assert len(briefings) == 1
        assert briefings[0].kind == "morning"

    def test_last_briefing(self):
        self.mem.record_briefing("morning", "Morning text")
        self.mem.record_briefing("evening", "Evening text")
        assert self.mem.last_briefing().kind == "evening"
        assert self.mem.last_briefing("morning").text == "Morning text"

    def test_last_briefing_empty(self):
        assert self.mem.last_briefing() is None

    def test_record_and_retrieve_recommendation(self):
        self.mem.record_recommendation("Query text", "command_deck", "Response text")
        recs = self.mem.recent_recommendations()
        assert len(recs) == 1
        assert recs[0].query == "Query text"
        assert recs[0].room == "command_deck"

    def test_preferences(self):
        self.mem.set_preference("briefing_style", "concise")
        assert self.mem.get_preference("briefing_style") == "concise"
        assert self.mem.get_preference("nonexistent") is None

    def test_recent_recommendations_limit(self):
        for i in range(10):
            self.mem.record_recommendation(f"Q{i}", "room", f"R{i}")
        assert len(self.mem.recent_recommendations(limit=3)) == 3

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
