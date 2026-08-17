from __future__ import annotations

import logging
import time
from typing import Any, Optional

from services.ai.ai_service import AIService
from services.ollo.briefing import BriefingGenerator
from services.ollo.context import ContextBuilder, OLLOContext
from services.ollo.i18n_fallback import ai_unavailable_message
from services.ollo.memory import CommanderMemory
from services.ollo.mission_profile import get_profile
from services.ollo.parser import OLLOBriefing, OLLOResponse, parse_response
from services.ollo.personality import get_system_prompt
from services.ollo.planner import Plan, Planner

logger = logging.getLogger(__name__)


class OLLOService:

    def __init__(
        self,
        ai_service: AIService,
        context_builder: ContextBuilder | None = None,
        planner: Planner | None = None,
        briefing_generator: BriefingGenerator | None = None,
        memory: CommanderMemory | None = None,
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

    def greet(self, room_id: str = "command_deck", language: str = "en") -> OLLOResponse:
        start = time.perf_counter()
        profile = get_profile(room_id)
        plan = self._planner.plan_greet(room_id)
        context = self._context.build(plan.context_keys, room=room_id)

        from services.ollo.prompts.greeting import get_greeting

        system_prompt = get_system_prompt(language)
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
            "OLLO greet result | room=%s | duration_ms=%s | tokens_in=%s | tokens_out=%s | retries=%s | error=%s",
            room_id, round(elapsed, 2), result.tokens_in, result.tokens_out, result.retries,
            result.error if result.error else "none",
        )

        # Same silent-empty-response gap as query()/briefing(): a fully
        # retried-out AI call returns content="" with the error detail only
        # in .error -- without this, the founder sees a blank welcome
        # message with no indication the AI service actually failed.
        content = result.content
        if result.error and not content:
            content = ai_unavailable_message(result.error, language)

        response = parse_response(
            raw_text=content,
            room=room_id,
            provider=result.provider,
            model=result.model,
            duration_ms=elapsed,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
        )

        return response

    def query(self, query: str, room_id: str = "command_deck", language: str = "en") -> OLLOResponse:
        start = time.perf_counter()
        profile = get_profile(room_id)
        plan = self._planner.plan_query(room_id, query)
        context = self._context.build(plan.context_keys, room=room_id)

        from services.ollo.prompts.rooms import room_query

        system_prompt = _profile_prompt(profile, language)
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
            "OLLO query result | room=%s | duration_ms=%s | tokens_in=%s | tokens_out=%s | retries=%s | error=%s",
            room_id, round(elapsed, 2), result.tokens_in, result.tokens_out, result.retries,
            result.error if result.error else "none",
        )

        # When the AI provider exhausts its retries (e.g. rate-limited),
        # GenerationResult.content is "" but the request still succeeds at
        # the HTTP layer -- without this check the founder sees a silent
        # empty response with no indication anything went wrong.
        content = result.content
        if result.error and not content:
            content = ai_unavailable_message(result.error, language)

        self._memory.record_recommendation(query, room_id, content)

        # Detect route intents based on simple keyword extraction (English + Turkish)
        intent_route = None
        q_lower = query.lower()
        if any(kw in q_lower for kw in ["portföy", "portfolio", "portfoy"]):
            intent_route = "/portfolio"
        elif any(kw in q_lower for kw in ["risk", "exposure"]):
            intent_route = "/risk"
        elif any(kw in q_lower for kw in ["taram", "scanner", "taray"]):
            intent_route = "/scanner"
        elif any(kw in q_lower for kw in ["analitik", "analytics", "analiz"]):
            intent_route = "/analytics"
        elif any(kw in q_lower for kw in ["journal", "gunluk", "günlük"]):
            intent_route = "/journal"
        elif any(kw in q_lower for kw in ["sinyal", "signal"]):
            intent_route = "/signals"
        elif any(kw in q_lower for kw in ["karar", "decision"]):
            intent_route = "/decisions"
        elif any(kw in q_lower for kw in ["market", "piyasa"]):
            intent_route = "/market"

        response = parse_response(
            raw_text=content,
            room=room_id,
            provider=result.provider,
            model=result.model,
            duration_ms=elapsed,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            intent_route=intent_route,
        )

        return response

    def briefing(self, kind: str = "morning", room_id: str = "command_deck", language: str = "en") -> OLLOBriefing:
        plan = self._planner.plan_briefing(room_id, kind)
        context = self._context.build(plan.context_keys, room=room_id)

        logger.info(
            "OLLO briefing | kind=%s | room=%s | context=%s",
            kind, room_id, context.summary_line(),
        )

        briefing = self._briefing.generate(plan, context, language=language)

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


def _profile_prompt(profile, language: str = "en") -> str:
    return f"""{get_system_prompt(language)}

You are currently in {profile.display_name}.

Mission purpose: {profile.purpose}

Your tone should be {profile.tone}.

Briefing style: {profile.briefing_style}

All responses must be grounded in the context data provided. Do not invent data.
"""
