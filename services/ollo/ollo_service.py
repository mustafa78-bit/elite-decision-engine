from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from services.ai.ai_service import AIService
from services.ollo.briefing import BriefingGenerator
from services.ollo.context import ContextBuilder, OLLOContext
from services.ollo.memory import CommanderMemory
from services.ollo.mission_profile import get_profile
from services.ollo.parser import OLLOBriefing, OLLOResponse, parse_response
from services.ollo.personality import get_system_prompt
from services.ollo.planner import Planner, Plan

from decision.kernel.FounderOS import FounderOS
from decision.kernel.KnowledgeGraph import KnowledgeGraph

logger = logging.getLogger(__name__)


class OLLOService:

    def __init__(
        self,
        ai_service: AIService,
        context_builder: Optional[ContextBuilder] = None,
        planner: Optional[Planner] = None,
        briefing_generator: Optional[BriefingGenerator] = None,
        memory: Optional[CommanderMemory] = None,
    ) -> None:
        self._ai = ai_service
        self._context = context_builder or ContextBuilder()
        self._planner = planner or Planner()
        self._briefing = briefing_generator or BriefingGenerator(ai_service)
        self._memory = memory or CommanderMemory()

    @property
    def memory(self) -> CommanderMemory:
        return self._memory

    @property
    def ai_service(self) -> AIService:
        return self._ai

    def greet(self, room_id: str = "command_deck") -> OLLOResponse:
        start = time.perf_counter()
        profile = get_profile(room_id)
        plan = self._planner.plan_greet(room_id)
        context = self._context.build(plan.context_keys, room=room_id)

        from services.ollo.prompts.greeting import get_greeting

        system_prompt = get_system_prompt()
        user_prompt = get_greeting(room_id, context.to_dict())

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(
            "OLLO greet | room=%s | profile=%s | context=%s",
            room_id, profile.room_id, context.summary_line(),
        )

        result = self._ai.chat(messages)
        elapsed = (time.perf_counter() - start) * 1000

        logger.info(
            "OLLO greet result | room=%s | duration_ms=%s | tokens_in=%s | tokens_out=%s | retries=%s",
            room_id, round(elapsed, 2), result.tokens_in, result.tokens_out, result.retries,
        )

        response = parse_response(
            raw_text=result.content,
            room=room_id,
            provider=result.provider,
            model=result.model,
            duration_ms=elapsed,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
        )

        return response

    def query(self, query: str, room_id: str = "command_deck") -> OLLOResponse:
        start = time.perf_counter()
        profile = get_profile(room_id)

        # Check if query matches a core executive question from FounderOS or SPRINT 11
        KNOWN_EXECUTIVE_KEYS = {
            "what_changed_overnight",
            "what_deserves_attention",
            "what_should_i_ignore",
            "which_risks_increased",
            "which_opportunities_appeared",
            "which_decisions_succeeded",
            "which_decisions_failed",
            "what_patterns_emerged",
            "what_should_i_do_first_today",
            "what_should_i_absolutely_avoid_today",
        }
        norm_key = query.lower().replace("?", "").replace(" ", "_").replace("'", "")
        is_executive = (norm_key in KNOWN_EXECUTIVE_KEYS) or any(k in norm_key for k in ("özetle", "know_today", "good_morning", "günaydın"))

        if is_executive:
            fos = FounderOS()
            executive_ans = fos.query(query)

            # Found custom executive response
            raw_text = f"**Executive Institutional Memory Answer:**\n{executive_ans['answer']}\n\n**Actionability:**\n{executive_ans['actionability']}"
            elapsed = (time.perf_counter() - start) * 1000

            # Record command action in memory
            fos.record_executive_action({
                "action": f"OLLO Query: {query}",
                "result": "INSTANT_EXECUTIVE_MATCH"
            })

            return OLLOResponse(
                text=raw_text,
                room=room_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="FounderOS",
                model="Executive-Memory-v2",
                duration_ms=elapsed,
                tokens_in=0,
                tokens_out=0,
                sections=[]
            )

        plan = self._planner.plan_query(room_id, query)
        context = self._context.build(plan.context_keys, room=room_id)

        from services.ollo.prompts.rooms import room_query

        system_prompt = _profile_prompt(profile)
        user_prompt = room_query(room_id, context.to_dict(), query)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(
            "OLLO query | room=%s | profile=%s | context=%s | query_len=%s",
            room_id, profile.room_id, context.summary_line(), len(query),
        )

        result = self._ai.chat(messages)
        elapsed = (time.perf_counter() - start) * 1000

        logger.info(
            "OLLO query result | room=%s | duration_ms=%s | tokens_in=%s | tokens_out=%s | retries=%s",
            room_id, round(elapsed, 2), result.tokens_in, result.tokens_out, result.retries,
        )

        self._memory.record_recommendation(query, room_id, result.content)

        response = parse_response(
            raw_text=result.content,
            room=room_id,
            provider=result.provider,
            model=result.model,
            duration_ms=elapsed,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
        )

        return response

    def briefing(self, kind: str = "morning", room_id: str = "command_deck") -> OLLOBriefing:
        start = time.perf_counter()

        # If morning briefing, ground with FounderOS Brief
        if kind == "morning":
            fos = FounderOS()
            brief = fos.generate_brief()

            # Ground directly with stable morning brief
            raw_brief_text = f"""# EXECUTIVE MORNING BRIEFING
**Status**: ACTIVE | **Time**: {brief.timestamp}

### 1. Executive Summary
{brief.executive_summary}

### 2. Market Condition
{brief.market_summary}

### 3. Portfolio Allocation
{brief.portfolio_summary}

### 4. Learning & Calibrations
{brief.learning_summary}
{brief.calibration_summary}

### 5. Recommended Actions
""" + "\n".join([f"- {a}" for e, a in enumerate(brief.recommended_actions)]) + """

### 6. Today's Strategic Priorities
""" + "\n".join([f"- {p}" for e, p in enumerate(brief.todays_priorities)])

            elapsed = (time.perf_counter() - start) * 1000
            self._memory.record_briefing(kind, raw_brief_text)

            return OLLOBriefing(
                kind=kind,
                title="Morning Briefing",
                text=raw_brief_text,
                timestamp=brief.timestamp,
                provider="FounderOS",
                model="Executive-Brain-v2",
                duration_ms=elapsed,
                tokens_in=0,
                tokens_out=0
            )

        plan = self._planner.plan_briefing(room_id, kind)
        context = self._context.build(plan.context_keys, room=room_id)

        logger.info(
            "OLLO briefing | kind=%s | room=%s | context=%s",
            kind, room_id, context.summary_line(),
        )

        briefing = self._briefing.generate(plan, context)
        elapsed = (time.perf_counter() - start) * 1000

        self._memory.record_briefing(kind, briefing.text)

        return briefing

    def status(self) -> dict:
        health = self._ai.health()
        profile = get_profile("command_deck")
        mem_status = self._memory.status()

        return {
            "provider": health.provider if health.connected else "unavailable",
            "model": health.model if health.connected else "unavailable",
            "current_mission_profile": profile.room_id,
            "current_room": "command_deck",
            "ai_health": {
                "connected": health.connected,
                "latency_ms": health.latency_ms,
                "error": health.error,
            },
            "memory": mem_status,
        }


def _profile_prompt(profile) -> str:
    return f"""{get_system_prompt()}

You are currently in {profile.display_name}.

Mission purpose: {profile.purpose}

Your tone should be {profile.tone}.

Briefing style: {profile.briefing_style}

All responses must be grounded in the context data provided. Do not invent data.
"""
