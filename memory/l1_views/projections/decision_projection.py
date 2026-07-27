import logging
from typing import Any, Dict, List, Callable
from database import get_session
from memory.l1_views.base import BaseProjection

logger = logging.getLogger(__name__)


class DecisionProjection(BaseProjection):
    """L1 Materialized Projection for AI Decisions."""

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self.session_factory = session_factory

    @property
    def projection_name(self) -> str:
        return "DecisionProjection"

    def supported_event_types(self) -> List[str]:
        return ["DecisionExplanationGenerated", "DecisionOutcomeUpdated"]

    def apply(self, event) -> None:
        pass

    def rebuild(self) -> None:
        pass

    def snapshot(self) -> Dict[str, Any]:
        return {}

    def restore_snapshot(self, state) -> None:
        pass

    def validate(self) -> bool:
        return True

    def health(self) -> Dict[str, Any]:
        return {"status": "HEALTHY"}
