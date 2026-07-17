from typing import Any, Dict, List, Optional

from orderflow.models import OrderFlowEvent, Trade
from orderflow.analyzer import (
    DeltaTracker,
    CVDAnalyzer,
    AggressiveOrderDetector,
    VolumeImbalanceAnalyzer,
    AbsorptionDetector,
    ExhaustionDetector,
)
from whale.logging import WhaleLogger

MAX_ORDERFLOW_EVENTS = 10000


class OrderFlowIntegration:

    def __init__(self):
        self.delta_tracker = DeltaTracker()
        self.cvd_analyzer = CVDAnalyzer()
        self.aggressive_detector = AggressiveOrderDetector()
        self.volume_imbalance = VolumeImbalanceAnalyzer()
        self.absorption = AbsorptionDetector()
        self.exhaustion = ExhaustionDetector()
        self.logger = WhaleLogger("orderflow_integration")
        self.enabled = True
        self.events: List[OrderFlowEvent] = []

    def process_trade(self, trade: Trade, mid_price: float) -> None:
        if not self.enabled or trade is None:
            return

        delta_point = self.delta_tracker.record_trade(trade, mid_price)
        if delta_point:
            self.cvd_analyzer.update(trade.asset, delta_point.delta)
            self.volume_imbalance.calculate(
                trade.asset,
                delta_point.buy_volume,
                delta_point.sell_volume,
            )

        agg = self.aggressive_detector.classify_trade(trade, mid_price)
        if agg.is_aggressive:
            self.events.append(
                OrderFlowEvent(
                    event_id=f"agg_{trade.trade_id}",
                    event_type="AGGRESSIVE_TRADE",
                    asset=trade.asset,
                    value=trade.size,
                    confidence=agg.confidence,
                    details={
                        "side": trade.side,
                        "price": trade.price,
                    },
                )
            )
            if len(self.events) > MAX_ORDERFLOW_EVENTS:
                del self.events[0]

    def get_features(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"orderflow_enabled": False}

        delta_summary = self.delta_tracker.get_delta_summary()
        cvd_trend = self.cvd_analyzer.get_cvd_trend()
        cvd_value = self.cvd_analyzer.get_cvd_value()
        agg_ratio = self.aggressive_detector.get_aggressive_ratio()
        vol_summary = self.volume_imbalance.get_summary()

        imb_confidence = self.volume_imbalance.get_imbalance_confidence()
        absorption_signals = self.absorption.get_recent(3)
        exhaustion_signals = self.exhaustion.get_recent(3)

        features = {
            "delta_trend": delta_summary["trend"],
            "cumulative_delta": round(delta_summary["cumulative_delta"], 4),
            "cvd_value": round(cvd_value, 4),
            "cvd_trend": cvd_trend,
            "aggressive_buy_ratio": agg_ratio["ratio"],
            "aggressive_total": agg_ratio["total"],
            "volume_imbalance_strength": vol_summary["avg_strength"],
            "imbalance_confidence": imb_confidence,
            "absorption_count": len(absorption_signals),
            "exhaustion_count": len(exhaustion_signals),
        }
        return {"orderflow_enabled": True, "orderflow_features": features}

    def get_contribution_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "type": e.event_type,
                "value": e.value,
                "confidence": e.confidence,
            }
            for e in self.events[-20:]
        ]

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "orderflow_available": False}
        self.logger.info(f"evaluate() — {len(self.events)} events, delta_trend={self.delta_tracker.get_delta_trend()}")
        return {
            "ok": True,
            "orderflow_available": True,
            "features": self.get_features(),
            "events_logged": len(self.events),
        }
