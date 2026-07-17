from typing import Any, Dict, List, Optional

from liquidity.models import LiquidityEvent
from liquidity.analyzer import ZoneManager, SweepDetector, ImbalanceAnalyzer
from whale.logging import WhaleLogger

MAX_LIQUIDITY_EVENTS = 10000


class LiquidityIntegration:

    def __init__(self):
        self.zone_manager = ZoneManager()
        self.sweep_detector = SweepDetector(self.zone_manager)
        self.imbalance_analyzer = ImbalanceAnalyzer()
        self.logger = WhaleLogger("liquidity_integration")
        self.enabled = True
        self.events: List[LiquidityEvent] = []

    def add_event(self, event: LiquidityEvent) -> None:
        if event is None:
            return
        self.events.append(event)
        self.logger.whale_event(event.event_type, {"asset": event.asset, "confidence": event.confidence})
        if len(self.events) > MAX_LIQUIDITY_EVENTS:
            del self.events[0]

    def get_liquidity_score(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"score": 0.0, "available": False}

        zones = self.zone_manager.get_active_zones()
        sweeps = self.sweep_detector.get_recent_sweeps()
        avg_imbalance = self.imbalance_analyzer.get_average_strength()

        zone_strength = sum(z.strength for z in zones) / max(len(zones), 1)
        sweep_count = len(sweeps)
        imbalance_strength = avg_imbalance

        score = (zone_strength * 2.0) + (min(sweep_count * 0.5, 3.0)) + (imbalance_strength * 1.0)
        score = round(min(score, 10.0), 4)

        return {
            "score": score,
            "available": True,
            "components": {
                "zone_strength": round(zone_strength, 4),
                "sweep_activity": min(sweep_count * 0.5, 3.0),
                "imbalance_strength": round(imbalance_strength, 4),
            },
        }

    def get_features(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"liquidity_enabled": False}

        zones = self.zone_manager.get_active_zones()
        sweeps = self.sweep_detector.get_recent_sweeps()
        avg_imbalance = self.imbalance_analyzer.get_average_strength()
        score_data = self.get_liquidity_score()

        features = {
            "active_zone_count": len(zones),
            "recent_sweep_count": len(sweeps),
            "average_imbalance_strength": round(avg_imbalance, 4),
            "total_events_logged": len(self.events),
            "liquidity_score": score_data["score"],
        }
        return {"liquidity_enabled": True, "liquidity_features": features}

    def get_contribution_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "type": e.event_type,
                "asset": e.asset,
                "price": e.price,
                "confidence": e.confidence,
            }
            for e in self.events[-20:]
        ]

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "liquidity_available": False}
        self.logger.info(f"evaluate() called — {len(self.events)} events, {len(self.zone_manager.get_active_zones())} zones")
        return {
            "ok": True,
            "liquidity_available": True,
            "features": self.get_features(),
            "events_logged": len(self.events),
        }
