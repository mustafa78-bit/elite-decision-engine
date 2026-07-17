from typing import Any, Dict, List, Optional

from market_structure.models import MarketStructureEvent, PriceCandle
from market_structure.analyzer import (
    SwingDetector,
    StructureAnalyzer,
    TrendStrengthAnalyzer,
)
from whale.logging import WhaleLogger

MAX_MS_EVENTS = 10000


class MarketStructureIntegration:

    def __init__(self):
        self.swing_detector = SwingDetector()
        self.structure_analyzer = StructureAnalyzer(self.swing_detector)
        self.trend_strength = TrendStrengthAnalyzer()
        self.logger = WhaleLogger("ms_integration")
        self.enabled = True
        self.events: List[MarketStructureEvent] = []

    def process_candle(self, candle: PriceCandle) -> None:
        if not self.enabled or candle is None:
            return

        swing = self.swing_detector.add_candle(candle)
        if swing:
            self.events.append(
                MarketStructureEvent(
                    event_id=f"swing_{candle.asset}_{len(self.events)}",
                    event_type="SWING_POINT",
                    asset=candle.asset,
                    price=swing.price,
                    confidence=swing.strength,
                    details={"point_type": swing.point_type},
                )
            )
            if len(self.events) > MAX_MS_EVENTS:
                del self.events[0]

    def detect_structure(self, asset: str, current_price: float) -> List[MarketStructureEvent]:
        if not self.enabled:
            return []

        detected = []
        bos = self.structure_analyzer.detect_bos(asset, current_price)
        if bos and self.structure_analyzer.events:
            detected.append(self.structure_analyzer.events[-1])

        choch = self.structure_analyzer.detect_choch(asset)
        if choch and self.structure_analyzer.events:
            detected.append(self.structure_analyzer.events[-1])

        return detected

    def get_features(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"market_structure_enabled": False}

        recent_swings = self.swing_detector.get_recent_swings(limit=10)
        swing_summary = self.swing_detector.get_swing_summary()

        trend_state = None
        if recent_swings:
            asset = recent_swings[-1].asset
            trend_state = self.structure_analyzer.get_latest_trend_state(asset)

        features = {
            "total_swings": swing_summary["total"],
            "swing_highs": swing_summary["highs"],
            "swing_lows": swing_summary["lows"],
            "structure_breaks": len(self.structure_analyzer.breaks),
        }

        if trend_state:
            features["trend"] = trend_state.trend
            features["trend_strength"] = trend_state.strength

        return {
            "market_structure_enabled": True,
            "market_structure_features": features,
        }

    def get_contribution_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "type": e.event_type,
                "price": e.price,
                "confidence": e.confidence,
            }
            for e in self.events[-20:]
        ]

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "market_structure_available": False}
        return {
            "ok": True,
            "market_structure_available": True,
            "features": self.get_features(),
            "events_logged": len(self.events),
        }
