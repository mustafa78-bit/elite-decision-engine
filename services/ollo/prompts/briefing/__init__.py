from services.ollo.prompts.briefing.morning import morning_briefing
from services.ollo.prompts.briefing.evening import evening_briefing
from services.ollo.prompts.briefing.market_update import market_update_briefing
from services.ollo.prompts.briefing.emergency import emergency_briefing
from services.ollo.prompts.briefing.mission import mission_briefing

BRIEFING_TEMPLATES: dict[str, callable] = {
    "morning": morning_briefing,
    "evening": evening_briefing,
    "market_update": market_update_briefing,
    "emergency": emergency_briefing,
    "mission": mission_briefing,
}


def get_briefing(kind: str, context: dict) -> str:
    template = BRIEFING_TEMPLATES.get(kind, morning_briefing)
    return template(context)
