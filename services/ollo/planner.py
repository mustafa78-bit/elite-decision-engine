from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from services.ollo.mission_profile import MissionProfile, get_profile

logger = logging.getLogger(__name__)

BRIEFING_KINDS = ("morning", "evening", "market_update", "emergency", "mission")


@dataclass
class Plan:
    mission_profile: MissionProfile
    context_keys: list[str]
    prompt_type: str
    prompt_template: str
    briefing_kind: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "mission_profile": self.mission_profile.room_id,
            "context_keys": self.context_keys,
            "prompt_type": self.prompt_type,
            "briefing_kind": self.briefing_kind,
        }


class Planner:

    def plan_query(self, room_id: str, query: str) -> Plan:
        profile = get_profile(room_id)
        context_keys = list(profile.allowed_context)

        logger.info(
            "Plan query | room=%s | context=%s",
            room_id, context_keys,
        )

        return Plan(
            mission_profile=profile,
            context_keys=context_keys,
            prompt_type="room_query",
            prompt_template=f"rooms/{room_id}",
        )

    def plan_briefing(self, room_id: str, kind: str) -> Plan:
        profile = get_profile(room_id)

        if kind not in BRIEFING_KINDS:
            kind = "morning"

        if kind == "emergency":
            context_keys = [
                "portfolio_summary", "portfolio_risk",
                "risk_metrics", "market_regime", "council_latest",
            ]
        elif kind == "mission":
            context_keys = list(profile.allowed_context)
        else:
            context_keys = [
                "portfolio_summary", "portfolio_performance",
                "market_regime", "risk_metrics", "council_latest",
                "scanner_signals", "whale_activity",
            ]

        logger.info(
            "Plan briefing | room=%s | kind=%s | context=%s",
            room_id, kind, context_keys,
        )

        return Plan(
            mission_profile=profile,
            context_keys=context_keys,
            prompt_type="briefing",
            prompt_template=f"briefing/{kind}",
            briefing_kind=kind,
        )

    def plan_greet(self, room_id: str) -> Plan:
        profile = get_profile(room_id)
        context_keys = ["portfolio_summary", "risk_metrics"]

        logger.info(
            "Plan greet | room=%s | context=%s",
            room_id, context_keys,
        )

        return Plan(
            mission_profile=profile,
            context_keys=context_keys,
            prompt_type="greeting",
            prompt_template=f"greeting/{room_id}",
        )
