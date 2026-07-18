from __future__ import annotations

import logging
import time
from typing import Any, Optional

from services.ai.ai_service import AIService
from services.ollo.context import OLLOContext
from services.ollo.parser import OLLOBriefing, parse_briefing
from services.ollo.personality import get_system_prompt
from services.ollo.planner import Plan

logger = logging.getLogger(__name__)


class BriefingGenerator:

    def __init__(self, ai_service: AIService) -> None:
        self._ai = ai_service

    def generate(
        self,
        plan: Plan,
        context: OLLOContext,
    ) -> OLLOBriefing:
        from services.ollo.prompts.briefing import get_briefing

        start = time.perf_counter()
        kind = plan.briefing_kind or "morning"

        system_prompt = get_system_prompt()
        user_prompt = get_briefing(kind, context.to_dict())

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(
            "BriefingGenerator | kind=%s | room=%s | model=%s",
            kind, plan.mission_profile.room_id, self._ai.model,
        )

        result = self._ai.chat(messages)
        elapsed = (time.perf_counter() - start) * 1000

        logger.info(
            "BriefingGenerator result | kind=%s | duration_ms=%s | tokens_in=%s | tokens_out=%s | retries=%s",
            kind, round(elapsed, 2), result.tokens_in, result.tokens_out, result.retries,
        )

        briefing = parse_briefing(
            kind=kind,
            raw_text=result.content,
            provider=result.provider,
            model=result.model,
            duration_ms=elapsed,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
        )

        return briefing
