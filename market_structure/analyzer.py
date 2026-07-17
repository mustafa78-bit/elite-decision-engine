from typing import Dict, List, Optional, Tuple

from market_structure.models import (
    PriceCandle,
    SwingPoint,
    StructureBreak,
    TrendState,
    MarketStructureEvent,
)
from whale.timestamp import TimestampHandler
from whale.logging import WhaleLogger


SWING_LOOKBACK = 5
SWING_STRENGTH_THRESHOLD = 0.5
MAX_CANDLES = 10000
MAX_SWING_POINTS = 10000


class SwingDetector:

    def __init__(self):
        self.candles: List[PriceCandle] = []
        self.swing_points: List[SwingPoint] = []
        self.logger = WhaleLogger("swing_detector")

    def add_candle(self, candle: PriceCandle) -> Optional[SwingPoint]:
        if candle is None:
            return None
        self.candles.append(candle)
        if len(self.candles) > MAX_CANDLES:
            del self.candles[0]
        check_idx = len(self.candles) - SWING_LOOKBACK - 1
        if check_idx >= SWING_LOOKBACK:
            return self._detect_swing(check_idx)
        return None

    def _detect_swing(self, index: int) -> Optional[SwingPoint]:
        if len(self.candles) < SWING_LOOKBACK * 2 + 1:
            return None
        if index < SWING_LOOKBACK or index >= len(self.candles) - SWING_LOOKBACK:
            return None

        current = self.candles[index]
        high = current.high
        low = current.low

        is_high = all(
            high > self.candles[i].high
            for i in range(index - SWING_LOOKBACK, index + SWING_LOOKBACK + 1)
            if i != index
        )
        is_low = all(
            low < self.candles[i].low
            for i in range(index - SWING_LOOKBACK, index + SWING_LOOKBACK + 1)
            if i != index
        )

        if not is_high and not is_low:
            return None

        point_type = "SWING_HIGH" if is_high else "SWING_LOW"
        price = high if is_high else low
        strength = self._calculate_strength(index, is_high)

        swing = SwingPoint(
            point_id=f"swing_{current.asset}_{len(self.swing_points)}_{int(TimestampHandler.utc_now().timestamp())}",
            asset=current.asset,
            point_type=point_type,
            price=price,
            index=index,
            strength=round(strength, 4),
        )
        self.swing_points.append(swing)
        if len(self.swing_points) > MAX_SWING_POINTS:
            del self.swing_points[0]
        return swing

    def _calculate_strength(self, index: int, is_high: bool) -> float:
        if len(self.candles) < SWING_LOOKBACK * 2 + 1:
            return 0.5
        current = self.candles[index]
        neighbors = [
            self.candles[i]
            for i in range(index - SWING_LOOKBACK, index + SWING_LOOKBACK + 1)
            if i != index and 0 <= i < len(self.candles)
        ]
        if not neighbors:
            return 0.5
        if is_high:
            avg_neighbor = sum(c.high for c in neighbors) / len(neighbors)
            return min((current.high - avg_neighbor) / avg_neighbor * 100, 1.0) if avg_neighbor > 0 else 0.5
        else:
            avg_neighbor = sum(c.low for c in neighbors) / len(neighbors)
            return min((avg_neighbor - current.low) / avg_neighbor * 100, 1.0) if avg_neighbor > 0 else 0.5

    def get_recent_swings(self, asset: Optional[str] = None, limit: int = 20) -> List[SwingPoint]:
        swings = self.swing_points[-limit:]
        if asset:
            swings = [s for s in swings if s.asset == asset]
        return swings

    def get_swing_summary(self, asset: Optional[str] = None) -> Dict[str, int]:
        swings = self.swing_points
        if asset:
            swings = [s for s in swings if s.asset == asset]
        return {
            "total": len(swings),
            "highs": sum(1 for s in swings if s.point_type == "SWING_HIGH"),
            "lows": sum(1 for s in swings if s.point_type == "SWING_LOW"),
        }


class StructureAnalyzer:

    def __init__(self, swing_detector: SwingDetector):
        self.swing_detector = swing_detector
        self.breaks: List[StructureBreak] = []
        self.events: List[MarketStructureEvent] = []
        self.logger = WhaleLogger("structure_analyzer")

    def classify_swing_sequence(self, asset: str) -> Tuple[List[str], List[str]]:
        highs: List[str] = []
        lows: List[str] = []
        swings = self.swing_detector.get_recent_swings(asset, limit=20)

        swing_highs = [s for s in swings if s.point_type == "SWING_HIGH"]
        swing_lows = [s for s in swings if s.point_type == "SWING_LOW"]

        for i in range(1, len(swing_highs)):
            if swing_highs[i].price > swing_highs[i - 1].price:
                highs.append("HH")
            else:
                highs.append("LH")

        for i in range(1, len(swing_lows)):
            if swing_lows[i].price > swing_lows[i - 1].price:
                lows.append("HL")
            else:
                lows.append("LL")

        return highs, lows

    def detect_bos(self, asset: str, current_price: float) -> Optional[StructureBreak]:
        swings = self.swing_detector.get_recent_swings(asset, limit=10)
        swing_highs = [s for s in swings if s.point_type == "SWING_HIGH"]
        swing_lows = [s for s in swings if s.point_type == "SWING_LOW"]

        if swing_highs:
            last_high = swing_highs[-1]
            if current_price > last_high.price * 1.001:
                break_event = StructureBreak(
                    break_id=f"bos_{asset}_{int(TimestampHandler.utc_now().timestamp())}",
                    asset=asset,
                    break_type="BOS",
                    direction="BULLISH",
                    price=current_price,
                    previous_swing_price=last_high.price,
                    confidence=0.7,
                )
                self.breaks.append(break_event)
                if len(self.breaks) > MAX_SWING_POINTS:
                    del self.breaks[0]
                self.events.append(MarketStructureEvent(
                    event_id=f"ms_bos_{int(TimestampHandler.utc_now().timestamp())}",
                    event_type="BREAK_OF_STRUCTURE",
                    asset=asset,
                    price=current_price,
                    confidence=0.7,
                    details={"direction": "BULLISH", "previous_high": last_high.price},
                ))
                if len(self.events) > MAX_SWING_POINTS:
                    del self.events[0]
                self.logger.whale_event("BOS_BULLISH", {"asset": asset, "price": current_price})
                return break_event

        if swing_lows:
            last_low = swing_lows[-1]
            if current_price < last_low.price * 0.999:
                break_event = StructureBreak(
                    break_id=f"bos_{asset}_{int(TimestampHandler.utc_now().timestamp())}",
                    asset=asset,
                    break_type="BOS",
                    direction="BEARISH",
                    price=current_price,
                    previous_swing_price=last_low.price,
                    confidence=0.7,
                )
                self.breaks.append(break_event)
                if len(self.breaks) > MAX_SWING_POINTS:
                    del self.breaks[0]
                self.events.append(MarketStructureEvent(
                    event_id=f"ms_bos_{int(TimestampHandler.utc_now().timestamp())}",
                    event_type="BREAK_OF_STRUCTURE",
                    asset=asset,
                    price=current_price,
                    confidence=0.7,
                    details={"direction": "BEARISH", "previous_low": last_low.price},
                ))
                if len(self.events) > MAX_SWING_POINTS:
                    del self.events[0]
                self.logger.whale_event("BOS_BEARISH", {"asset": asset, "price": current_price})
                return break_event

        return None

    def detect_choch(self, asset: str) -> Optional[StructureBreak]:
        highs, lows = self.classify_swing_sequence(asset)
        if len(highs) < 2 or len(lows) < 2:
            return None

        recent_highs = highs[-3:] if len(highs) >= 3 else highs
        recent_lows = lows[-3:] if len(lows) >= 3 else lows

        if all(h == "LH" for h in recent_highs) and all(l == "LL" for l in recent_lows):
            break_event = StructureBreak(
                break_id=f"choch_{asset}_{int(TimestampHandler.utc_now().timestamp())}",
                asset=asset,
                break_type="CHoCH",
                direction="BEARISH",
                price=0.0,
                confidence=0.6,
            )
            self.breaks.append(break_event)
            if len(self.breaks) > MAX_SWING_POINTS:
                del self.breaks[0]
            self.events.append(MarketStructureEvent(
                event_id=f"ms_choch_{int(TimestampHandler.utc_now().timestamp())}",
                event_type="CHANGE_OF_CHARACTER",
                asset=asset,
                confidence=0.6,
                details={"direction": "BEARISH", "highs": recent_highs, "lows": recent_lows},
            ))
            if len(self.events) > MAX_SWING_POINTS:
                del self.events[0]
            return break_event

        if all(h == "HH" for h in recent_highs) and all(l == "HL" for l in recent_lows):
            break_event = StructureBreak(
                break_id=f"choch_{asset}_{int(TimestampHandler.utc_now().timestamp())}",
                asset=asset,
                break_type="CHoCH",
                direction="BULLISH",
                price=0.0,
                confidence=0.6,
            )
            self.breaks.append(break_event)
            if len(self.breaks) > MAX_SWING_POINTS:
                del self.breaks[0]
            self.events.append(MarketStructureEvent(
                event_id=f"ms_choch_{int(TimestampHandler.utc_now().timestamp())}",
                event_type="CHANGE_OF_CHARACTER",
                asset=asset,
                confidence=0.6,
                details={"direction": "BULLISH", "highs": recent_highs, "lows": recent_lows},
            ))
            if len(self.events) > MAX_SWING_POINTS:
                del self.events[0]
            return break_event

        return None

    def get_latest_trend_state(self, asset: str) -> TrendState:
        highs, lows = self.classify_swing_sequence(asset)
        recent_highs = highs[-3:] if highs else []
        recent_lows = lows[-3:] if lows else []

        if recent_highs and all(h == "HH" for h in recent_highs):
            trend = "BULLISH"
        elif recent_lows and all(l == "LL" for l in recent_lows):
            trend = "BEARISH"
        elif recent_highs and all(h == "LH" for h in recent_highs):
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        swings = self.swing_detector.get_recent_swings(asset, limit=10)
        swing_high_prices = [s.price for s in swings if s.point_type == "SWING_HIGH"]
        swing_low_prices = [s.price for s in swings if s.point_type == "SWING_LOW"]

        strength = self._calculate_trend_strength(highs, lows)

        return TrendState(
            asset=asset,
            trend=trend,
            strength=round(strength, 4),
            swing_highs=swing_high_prices,
            swing_lows=swing_low_prices,
        )

    def _calculate_trend_strength(self, highs: List[str], lows: List[str]) -> float:
        total = len(highs) + len(lows)
        if total == 0:
            return 0.0
        bullish = sum(1 for h in highs if h == "HH") + sum(1 for l in lows if l == "HL")
        return bullish / total if total > 0 else 0.0


class TrendStrengthAnalyzer:

    def __init__(self):
        self.logger = WhaleLogger("trend_strength")

    def calculate(self, prices: List[float]) -> Dict[str, float]:
        if len(prices) < 2:
            return {"strength": 0.0, "direction": "NEUTRAL", "volatility": 0.0}

        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        avg_change = sum(changes) / len(changes)
        abs_changes = [abs(c) for c in changes]
        volatility = sum(abs_changes) / len(abs_changes)
        base_price = prices[0]
        normalized_change = avg_change / base_price if base_price > 0 else 0
        strength = min(abs(normalized_change) * 100, 1.0)

        direction = "BULLISH" if avg_change > 0 else "BEARISH" if avg_change < 0 else "NEUTRAL"

        return {
            "strength": round(strength, 4),
            "direction": direction,
            "volatility": round(volatility, 4),
        }
