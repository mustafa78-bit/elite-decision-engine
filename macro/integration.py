from typing import Any, Dict, List, Optional

from macro.models import FearGreedIndex, MacroEvent, EconomicIndicator, VixDxySnapshot
from macro.analyzer import FearGreedAnalyzer, MacroEventAnalyzer, VixDxyPlaceholder
from whale.logging import WhaleLogger

MAX_MACRO_EVENTS = 10000
MAX_INDICATORS = 10000


class MacroIntegration:

    def __init__(self):
        self.fear_greed = FearGreedAnalyzer()
        self.event_analyzer = MacroEventAnalyzer()
        self.vix_dxy = VixDxyPlaceholder()
        self.indicators: List[EconomicIndicator] = []
        self.logger = WhaleLogger("macro_integration")
        self.enabled = True
        self.events: List[MacroEvent] = []
        self._latest_fng_value: Optional[float] = None

    def process_fear_greed(self, value: float) -> FearGreedIndex:
        fg = self.fear_greed.evaluate(value)
        if self.enabled:
            self._latest_fng_value = value
            self.events.append(MacroEvent(
                event_id=f"fng_{int(value)}_{len(self.events)}",
                event_type="FEAR_GREED_INDEX",
                asset="GENERAL",
                title=f"Fear & Greed: {fg.classification} ({value})",
                value=value,
                confidence=fg.confidence if hasattr(fg, 'confidence') else self.fear_greed.calculate_confidence(value),
                details={"classification": fg.classification},
            ))
            if len(self.events) > MAX_MACRO_EVENTS:
                del self.events[0]
        return fg

    def process_macro_event(self, event: MacroEvent) -> Optional[MacroEvent]:
        if not self.enabled or event is None:
            return None
        processed = self.event_analyzer.process_event(event)
        if processed:
            self.events.append(processed)
            if len(self.events) > MAX_MACRO_EVENTS:
                del self.events[0]
        return processed

    def record_indicator(self, indicator: EconomicIndicator) -> EconomicIndicator:
        if indicator is None:
            return indicator
        self.indicators.append(indicator)
        if len(self.indicators) > MAX_INDICATORS:
            del self.indicators[0]
        return indicator

    def update_vix_dxy(self, vix: Optional[float] = None, dxy: Optional[float] = None) -> VixDxySnapshot:
        return self.vix_dxy.update(vix, dxy)

    def get_features(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"macro_enabled": False}

        fg_value = self._latest_fng_value if self._latest_fng_value is not None else 50
        fg_latest = self.fear_greed.evaluate(fg_value)
        fg_summary = {"classification": fg_latest.classification, "value": fg_value}

        macro_summary = self.event_analyzer.get_summary()
        vix_dxy_info = self.vix_dxy.get_summary()

        high_impact = self.event_analyzer.get_high_impact(5)
        high_impact_list = [
            {"title": e.title, "importance": e.importance, "asset": e.asset}
            for e in high_impact
        ]

        features = {
            "fear_greed": fg_summary,
            "total_events": macro_summary["total"],
            "high_impact_events": macro_summary["high_impact"],
            "avg_event_confidence": macro_summary["avg_confidence"],
            "indicators_count": len(self.indicators),
            "vix_dxy": vix_dxy_info,
            "upcoming_high_impact": high_impact_list,
        }

        return {
            "macro_enabled": True,
            "macro_features": features,
        }

    def get_contribution_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "type": e.event_type,
                "asset": e.asset,
                "importance": e.importance,
                "confidence": e.confidence,
            }
            for e in self.events[-20:]
        ]

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "macro_available": False}
        return {
            "ok": True,
            "macro_available": True,
            "features": self.get_features(),
            "events_logged": len(self.events),
        }
