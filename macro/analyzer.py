from datetime import datetime, timezone
from typing import Dict, List, Optional

from macro.models import FearGreedIndex, MacroEvent, VixDxySnapshot
from whale.logging import WhaleLogger
from whale.timestamp import TimestampHandler

MAX_EVENTS = 10000
MAX_SNAPSHOTS = 10000

IMPORTANCE_WEIGHTS = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 5,
}

MACRO_FRESHNESS_HOURS = 48


class FearGreedAnalyzer:

    def __init__(self):
        self.logger = WhaleLogger("fear_greed")

    def classify(self, value: float) -> str:
        if value <= 25:
            return "EXTREME_FEAR"
        elif value <= 45:
            return "FEAR"
        elif value <= 55:
            return "NEUTRAL"
        elif value <= 75:
            return "GREED"
        else:
            return "EXTREME_GREED"

    def calculate_confidence(self, value: float) -> float:
        distance = abs(value - 50) / 50.0
        return min(distance, 1.0)

    def evaluate(self, value: float) -> FearGreedIndex:
        clamped = max(0.0, min(value, 100.0))
        classification = self.classify(clamped)
        return FearGreedIndex(
            value=round(clamped, 2),
            classification=classification,
        )


class MacroEventAnalyzer:

    def __init__(self):
        self.events: List[MacroEvent] = []
        self.logger = WhaleLogger("macro_event_analyzer")

    def process_event(self, event: MacroEvent) -> MacroEvent:
        if event is None:
            return event
        event.confidence = self._calculate_confidence(event)
        self.events.append(event)
        if len(self.events) > MAX_EVENTS:
            del self.events[0]
        return event

    def _calculate_confidence(self, event: MacroEvent) -> float:
        importance_base = IMPORTANCE_WEIGHTS.get(event.importance, 2) / 5.0
        age_hours = self._age_hours(event.timestamp)
        freshness = max(0.0, 1.0 - (age_hours / MACRO_FRESHNESS_HOURS))
        conf = (importance_base * 0.6) + (freshness * 0.4)
        return round(min(conf, 1.0), 4)

    def _age_hours(self, dt: Optional[datetime]) -> float:
        if dt is None:
            return 0.0
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max((now - dt).total_seconds(), 0) / 3600.0

    def get_upcoming(
        self,
        asset: Optional[str] = None,
        min_importance: str = "LOW",
        limit: int = 20,
    ) -> List[MacroEvent]:
        min_weight = IMPORTANCE_WEIGHTS.get(min_importance, 1)
        result = [e for e in self.events if IMPORTANCE_WEIGHTS.get(e.importance, 1) >= min_weight]
        if asset:
            result = [e for e in result if e.asset == asset]
        return result[-limit:]

    def get_high_impact(self, limit: int = 20) -> List[MacroEvent]:
        return [e for e in self.events if e.importance in ("HIGH", "CRITICAL")][-limit:]

    def get_summary(self, asset: Optional[str] = None) -> Dict[str, object]:
        items = self.events
        if asset:
            items = [e for e in items if e.asset == asset]
        if not items:
            return {"total": 0, "high_impact": 0, "avg_confidence": 0.0}
        return {
            "total": len(items),
            "high_impact": sum(1 for e in items if e.importance in ("HIGH", "CRITICAL")),
            "avg_confidence": round(sum(e.confidence for e in items) / len(items), 4),
        }

    def is_fresh(self, event: MacroEvent, max_age_hours: int = MACRO_FRESHNESS_HOURS) -> bool:
        if event is None:
            return False
        return self._age_hours(event.timestamp) <= max_age_hours


class VixDxyPlaceholder:

    def __init__(self):
        self.snapshots: List[VixDxySnapshot] = []
        self.logger = WhaleLogger("vix_dxy_placeholder")

    def update(self, vix: Optional[float] = None, dxy: Optional[float] = None) -> VixDxySnapshot:
        snapshot = VixDxySnapshot(vix_value=vix, dxy_value=dxy)
        self.snapshots.append(snapshot)
        if len(self.snapshots) > MAX_SNAPSHOTS:
            del self.snapshots[0]
        return snapshot

    def get_latest(self) -> Optional[VixDxySnapshot]:
        return self.snapshots[-1] if self.snapshots else None

    def get_summary(self) -> Dict[str, Optional[float]]:
        latest = self.get_latest()
        if not latest:
            return {"vix": None, "dxy": None, "available": False}
        return {
            "vix": latest.vix_value,
            "dxy": latest.dxy_value,
            "available": True,
        }
