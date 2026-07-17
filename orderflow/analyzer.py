import uuid
from typing import Dict, List, Optional, Tuple

from orderflow.models import (
    Trade,
    DeltaPoint,
    VolumeImbalance,
    CVD,
    AggressiveOrder,
    AbsorptionSignal,
    ExhaustionSignal,
    OrderFlowEvent,
)
from whale.logging import WhaleLogger


IMBALANCE_THRESHOLD = 1.5
DELTA_DIVERGENCE_WINDOW = 10
MAX_POINTS = 10000
MAX_CVD_POINTS = 10000
MAX_AGGRESSIVE_ORDERS = 10000
MAX_IMBALANCES = 10000


class DeltaTracker:

    def __init__(self):
        self.points: List[DeltaPoint] = []
        self.cumulative_delta: float = 0.0
        self.logger = WhaleLogger("delta_tracker")

    def record_trade(self, trade: Trade, mid_price: float) -> DeltaPoint:
        if trade is None:
            return DeltaPoint(asset="UNKNOWN", buy_volume=0.0, sell_volume=0.0, delta=0.0, cumulative_delta=self.cumulative_delta)
        is_buy = trade.side.upper() == "BUY"
        is_sell = trade.side.upper() == "SELL"

        delta_value = trade.size if is_buy else -trade.size
        self.cumulative_delta += delta_value

        point = DeltaPoint(
            asset=trade.asset,
            buy_volume=trade.size if is_buy else 0.0,
            sell_volume=trade.size if is_sell else 0.0,
            delta=delta_value,
            cumulative_delta=self.cumulative_delta,
        )
        self.points.append(point)
        if len(self.points) > MAX_POINTS:
            del self.points[0]
        return point

    def get_current_delta(self) -> float:
        if not self.points:
            return 0.0
        return self.points[-1].delta

    def get_cumulative_delta(self) -> float:
        return self.cumulative_delta

    def get_delta_trend(self, window: int = 10) -> str:
        if window <= 0:
            return "NEUTRAL"
        recent = self.points[-window:]
        if len(recent) < 2:
            return "NEUTRAL"
        avg = sum(p.delta for p in recent) / len(recent)
        if avg > 0.1:
            return "POSITIVE"
        elif avg < -0.1:
            return "NEGATIVE"
        return "NEUTRAL"

    def get_delta_summary(self) -> Dict[str, object]:
        return {
            "current_delta": self.get_current_delta(),
            "cumulative_delta": self.get_cumulative_delta(),
            "trend": self.get_delta_trend(),
            "total_points": len(self.points),
        }


class CVDAnalyzer:

    def __init__(self):
        self.cvd_points: List[CVD] = []
        self.logger = WhaleLogger("cvd_analyzer")

    def update(self, asset: str, delta: float) -> CVD:
        if not asset:
            asset = "UNKNOWN"
        last_value = self.cvd_points[-1].value if self.cvd_points else 0.0
        value = last_value + delta

        trend = self._calculate_trend()
        divergence = self._detect_divergence(asset)

        cvd = CVD(
            asset=asset,
            value=round(value, 4),
            trend=trend,
            divergence=divergence,
        )
        self.cvd_points.append(cvd)
        if len(self.cvd_points) > MAX_CVD_POINTS:
            del self.cvd_points[0]
        return cvd

    def _calculate_trend(self, window: int = 5) -> str:
        if window <= 0:
            return "NEUTRAL"
        recent = self.cvd_points[-window:]
        if len(recent) < 2:
            return "NEUTRAL"
        slope = recent[-1].value - recent[0].value
        if slope > 0.5:
            return "RISING"
        elif slope < -0.5:
            return "FALLING"
        return "NEUTRAL"

    def _detect_divergence(self, asset: str) -> Optional[str]:
        if len(self.cvd_points) < DELTA_DIVERGENCE_WINDOW:
            return None
        recent = self.cvd_points[-DELTA_DIVERGENCE_WINDOW:]
        current_trend = self._calculate_trend(3)
        if current_trend == "RISING" and recent[-1].value < recent[-3].value:
            return "BEARISH_DIVERGENCE"
        if current_trend == "FALLING" and recent[-1].value > recent[-3].value:
            return "BULLISH_DIVERGENCE"
        return None

    def get_cvd_value(self) -> float:
        return self.cvd_points[-1].value if self.cvd_points else 0.0

    def get_cvd_trend(self) -> str:
        return self.cvd_points[-1].trend if self.cvd_points else "NEUTRAL"


class AggressiveOrderDetector:

    def __init__(self):
        self.aggressive_orders: List[AggressiveOrder] = []
        self.logger = WhaleLogger("aggressive_detector")

    def classify_trade(self, trade: Trade, mid_price: float) -> AggressiveOrder:
        is_buy_aggressive = trade.side.upper() == "BUY" and trade.price >= mid_price
        is_sell_aggressive = trade.side.upper() == "SELL" and trade.price <= mid_price
        is_aggressive = is_buy_aggressive or is_sell_aggressive

        confidence = self._calculate_confidence(trade, mid_price)

        agg_order = AggressiveOrder(
            order_id=f"agg_{trade.trade_id}",
            asset=trade.asset,
            side=trade.side,
            size=trade.size,
            price=trade.price,
            is_aggressive=is_aggressive,
            confidence=confidence,
        )
        if is_aggressive:
            self.aggressive_orders.append(agg_order)
            if len(self.aggressive_orders) > MAX_AGGRESSIVE_ORDERS:
                del self.aggressive_orders[0]
            self.logger.whale_event("AGGRESSIVE_ORDER", {
                "asset": trade.asset,
                "side": trade.side,
                "size": trade.size,
            })
        return agg_order

    def _calculate_confidence(self, trade: Trade, mid_price: float) -> float:
        if trade is None or mid_price is None:
            return 0.5
        spread = abs(trade.price - mid_price) / mid_price if mid_price > 0 else 0
        base = 0.5
        if spread > 0.001:
            base += 0.2
        if trade.size > 10000:
            base += 0.15
        if trade.size > 100000:
            base += 0.1
        return min(base, 1.0)

    def get_aggressive_ratio(
        self, asset: Optional[str] = None, window: int = 50
    ) -> Dict[str, float]:
        if window <= 0:
            return {"ratio": 0.0, "buy_count": 0, "sell_count": 0, "total": 0}
        recent = self.aggressive_orders[-window:]
        if asset:
            recent = [o for o in recent if o.asset == asset]
        if not recent:
            return {"ratio": 0.0, "buy_count": 0, "sell_count": 0, "total": 0}
        buys = sum(1 for o in recent if o.side.upper() == "BUY")
        sells = sum(1 for o in recent if o.side.upper() == "SELL")
        total = len(recent)
        return {
            "ratio": round(buys / total if total > 0 else 0, 4),
            "buy_count": buys,
            "sell_count": sells,
            "total": total,
        }


class VolumeImbalanceAnalyzer:

    def __init__(self):
        self.imbalances: List[VolumeImbalance] = []
        self.logger = WhaleLogger("volume_imbalance")

    def calculate(
        self, asset: str, buy_volume: float, sell_volume: float, timeframe: str = "1m"
    ) -> VolumeImbalance:
        if buy_volume <= 0 or sell_volume <= 0:
            ratio = 1.0
            direction = "NEUTRAL"
        elif buy_volume > sell_volume:
            ratio = buy_volume / sell_volume
            direction = "BULLISH"
        elif sell_volume > buy_volume:
            ratio = sell_volume / buy_volume
            direction = "BEARISH"
        else:
            ratio = 1.0
            direction = "NEUTRAL"

        strength = min((ratio - 1.0) / 3.0, 1.0) if ratio > 1.0 else 0.0

        imb = VolumeImbalance(
            asset=asset,
            timeframe=timeframe,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            ratio=round(ratio, 4),
            direction=direction,
            strength=round(strength, 4),
        )
        self.imbalances.append(imb)
        if len(self.imbalances) > MAX_IMBALANCES:
            del self.imbalances[0]
        return imb

    def get_significant(
        self,
        asset: Optional[str] = None,
        threshold: float = IMBALANCE_THRESHOLD,
        limit: int = 20,
    ) -> List[VolumeImbalance]:
        result = [i for i in self.imbalances if i.ratio >= threshold]
        if asset:
            result = [i for i in result if i.asset == asset]
        return result[-limit:]

    def get_imbalance_confidence(self, asset: Optional[str] = None) -> float:
        items = self.imbalances
        if asset:
            items = [i for i in items if i.asset == asset]
        if not items:
            return 0.0
        recent = items[-10:]
        avg_strength = sum(i.strength for i in recent) / len(recent)
        significant_ratio = sum(1 for i in recent if i.ratio >= IMBALANCE_THRESHOLD) / max(len(recent), 1)
        confidence = (avg_strength * 0.6) + (significant_ratio * 0.4)
        return round(min(confidence, 1.0), 4)

    def get_summary(self, asset: Optional[str] = None) -> Dict[str, float]:
        items = self.imbalances
        if asset:
            items = [i for i in items if i.asset == asset]
        if not items:
            return {"avg_strength": 0.0, "total": 0}
        return {
            "avg_strength": round(sum(i.strength for i in items) / len(items), 4),
            "total": len(items),
        }


class AbsorptionDetector:

    def __init__(self):
        self.signals: List[AbsorptionSignal] = []
        self.logger = WhaleLogger("absorption_detector")

    def detect(
        self,
        asset: str,
        buy_volume: float,
        sell_volume: float,
        price_change: float,
    ) -> Optional[AbsorptionSignal]:
        if buy_volume <= 0 or sell_volume <= 0:
            return None
        total = buy_volume + sell_volume
        if total == 0:
            return None
        imbalance_ratio = abs(buy_volume - sell_volume) / total
        if imbalance_ratio < 0.2 and total > 1_000_000:
            direction = "BULLISH" if price_change > 0 else "BEARISH"
            strength = min((1.0 - imbalance_ratio) * 0.8, 1.0)
            signal = AbsorptionSignal(
                asset=asset,
                direction=direction,
                strength=round(strength, 4),
                confidence=round(0.5 + strength * 0.3, 4),
                buy_volume=buy_volume,
                sell_volume=sell_volume,
            )
            self.signals.append(signal)
            self.logger.whale_event("ABSORPTION_DETECTED", {"asset": asset, "direction": direction})
            return signal
        return None

    def get_recent(self, limit: int = 10) -> List[AbsorptionSignal]:
        return self.signals[-limit:]


class ExhaustionDetector:

    def __init__(self):
        self.signals: List[ExhaustionSignal] = []
        self.logger = WhaleLogger("exhaustion_detector")

    def detect(
        self,
        asset: str,
        price_change: float,
        volume_change: float,
        prior_volume: float,
    ) -> Optional[ExhaustionSignal]:
        if prior_volume <= 0:
            return None
        volume_drop_ratio = abs(volume_change) / prior_volume
        if volume_drop_ratio > 0.4 and abs(price_change) < 0.01:
            direction = "BULLISH_EXHAUSTION" if price_change > 0 else "BEARISH_EXHAUSTION"
            strength = min(volume_drop_ratio * 0.8, 1.0)
            signal = ExhaustionSignal(
                asset=asset,
                direction=direction,
                strength=round(strength, 4),
                confidence=round(0.4 + strength * 0.4, 4),
                price_change=price_change,
                volume_drop=volume_drop_ratio,
            )
            self.signals.append(signal)
            self.logger.whale_event("EXHAUSTION_DETECTED", {"asset": asset, "direction": direction})
            return signal
        return None

    def get_recent(self, limit: int = 10) -> List[ExhaustionSignal]:
        return self.signals[-limit:]
