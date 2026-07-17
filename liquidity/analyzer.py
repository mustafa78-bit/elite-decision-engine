import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from liquidity.models import (
    LiquidityZone,
    LiquiditySweep,
    LiquidityImbalance,
    LiquidityEvent,
)
from whale.timestamp import TimestampHandler
from whale.logging import WhaleLogger


ZONE_TOUCH_THRESHOLD = 0.005
SWEEP_CONFIRMATION_DISTANCE = 0.01
DEFAULT_IMBALANCE_THRESHOLD = 1.5
MAX_SWEEPS = 10000
MAX_IMBALANCES = 10000


class ZoneManager:

    def __init__(self):
        self.zones: Dict[str, LiquidityZone] = {}
        self.logger = WhaleLogger("zone_manager")

    def create_zone(
        self,
        asset: str,
        zone_type: str,
        price_low: float,
        price_high: float,
        strength: float = 0.5,
    ) -> LiquidityZone:
        """Create a liquidity zone with asset, type, price range, and optional strength."""
        zone_id = f"zone_{asset}_{len(self.zones)}_{int(TimestampHandler.utc_now().timestamp())}"
        zone = LiquidityZone(
            zone_id=zone_id,
            asset=asset,
            zone_type=zone_type,
            price_low=min(price_low, price_high),
            price_high=max(price_low, price_high),
            strength=max(0.0, min(1.0, strength)),
        )
        self.zones[zone_id] = zone
        self.logger.info(f"Zone created: {zone_id} ({zone_type}) @ [{price_low:.2f}-{price_high:.2f}]")
        return zone

    def test_zone(self, zone_id: str, price: float) -> bool:
        """Check if price is within touch threshold of zone midpoint."""
        if not zone_id:
            return False
        zone = self.zones.get(zone_id)
        if zone is None or not zone.is_active:
            return False
        threshold = ZONE_TOUCH_THRESHOLD
        mid = (zone.price_low + zone.price_high) / 2.0
        if mid == 0:
            mid = 1e-10
        distance = abs(price - mid) / mid
        return distance <= threshold

    def touch_zone(self, zone_id: str, price: float) -> Optional[LiquidityEvent]:
        """Record a zone touch, increasing its strength if price is within threshold."""
        if not zone_id:
            return None
        zone = self.zones.get(zone_id)
        if zone is None or not zone.is_active:
            return None
        if self.test_zone(zone_id, price):
            zone.touches += 1
            zone.last_tested = TimestampHandler.utc_now()
            zone.strength = min(1.0, zone.strength + 0.05 * zone.touches)
            return LiquidityEvent(
                event_id=f"touch_{zone_id}_{int(TimestampHandler.utc_now().timestamp())}",
                event_type="ZONE_TOUCH",
                asset=zone.asset,
                price=price,
                confidence=zone.strength,
                details={
                    "zone_id": zone_id,
                    "zone_type": zone.zone_type,
                    "touches": zone.touches,
                },
            )
        return None

    def deactivate_zone(self, zone_id: str) -> bool:
        """Deactivate a zone by zone_id, returning True if found."""
        if not zone_id:
            return False
        zone = self.zones.get(zone_id)
        if zone is None:
            return False
        zone.is_active = False
        self.logger.info(f"Zone deactivated: {zone_id}")
        return True

    def get_active_zones(self, asset: Optional[str] = None) -> List[LiquidityZone]:
        """Return active zones, optionally filtered by asset."""
        zones = [z for z in self.zones.values() if z.is_active]
        if asset:
            zones = [z for z in zones if z.asset == asset]
        return zones

    def get_zone_summary(self, asset: Optional[str] = None) -> Dict[str, int]:
        zones = self.get_active_zones(asset)
        summary: Dict[str, int] = {"total": len(zones), "support": 0, "resistance": 0, "supply": 0, "demand": 0}
        for z in zones:
            t = z.zone_type.lower()
            summary[t] = summary.get(t, 0) + 1
        return summary


class SweepDetector:

    def __init__(self, zone_manager: ZoneManager):
        self.zone_manager = zone_manager
        self.sweeps: List[LiquiditySweep] = []
        self.logger = WhaleLogger("sweep_detector")

    def detect_sweep(
        self,
        asset: str,
        price: float,
        volume: float,
        direction: str,
    ) -> Optional[LiquiditySweep]:
        """Detect if price swept a liquidity zone, returning a LiquiditySweep or None."""
        zones = self.zone_manager.get_active_zones(asset)
        for zone in zones:
            if not self._is_swept(zone, price, direction):
                continue
            sweep_id = f"sweep_{asset}_{len(self.sweeps)}_{int(TimestampHandler.utc_now().timestamp())}"
            sweep = LiquiditySweep(
                sweep_id=sweep_id,
                asset=asset,
                zone_id=zone.zone_id,
                direction=direction,
                price=price,
                volume=volume,
                confidence=self._calculate_sweep_confidence(zone, price, volume),
                details={"zone_type": zone.zone_type, "zone_strength": zone.strength},
            )
            self.sweeps.append(sweep)
            if len(self.sweeps) > MAX_SWEEPS:
                del self.sweeps[0]
            self.zone_manager.deactivate_zone(zone.zone_id)
            self.logger.whale_event("LIQUIDITY_SWEEP", {
                "asset": asset,
                "zone": zone.zone_id,
                "price": price,
                "direction": direction,
            })
            return sweep
        return None

    def _is_swept(self, zone: LiquidityZone, price: float, direction: str) -> bool:
        if direction.upper() == "BULLISH":
            return price > zone.price_high * (1 + SWEEP_CONFIRMATION_DISTANCE)
        elif direction.upper() == "BEARISH":
            return price < zone.price_low * (1 - SWEEP_CONFIRMATION_DISTANCE)
        return False

    def _calculate_sweep_confidence(self, zone: LiquidityZone, price: float, volume: float) -> float:
        base = zone.strength * 0.5
        volume_factor = min(volume / 1000000.0, 0.3)
        distance = abs(price - (zone.price_low + zone.price_high) / 2.0)
        distance_factor = min(distance / zone.price_low if zone.price_low > 0 else 0, 0.2)
        return min(base + volume_factor + distance_factor, 1.0)

    def get_recent_sweeps(self, asset: Optional[str] = None, limit: int = 20) -> List[LiquiditySweep]:
        sweeps = self.sweeps[-limit:]
        if asset:
            sweeps = [s for s in sweeps if s.asset == asset]
        return sweeps


class ImbalanceAnalyzer:

    def __init__(self):
        self.imbalances: List[LiquidityImbalance] = []
        self.logger = WhaleLogger("imbalance_analyzer")

    def calculate_imbalance(self, asset: str, bid_volume: float, ask_volume: float) -> LiquidityImbalance:
        """Calculate order book imbalance from bid/ask volumes."""
        if bid_volume <= 0 or ask_volume <= 0:
            ratio = 1.0
            direction = "NEUTRAL"
        elif bid_volume > ask_volume:
            ratio = bid_volume / ask_volume
            direction = "BULLISH"
        elif ask_volume > bid_volume:
            ratio = ask_volume / bid_volume
            direction = "BEARISH"
        else:
            ratio = 1.0
            direction = "NEUTRAL"

        strength = min((ratio - 1.0) / 2.0, 1.0) if ratio > 1.0 else 0.0

        imbalance = LiquidityImbalance(
            asset=asset,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            ratio=round(ratio, 4),
            direction=direction,
            strength=round(strength, 4),
        )
        self.imbalances.append(imbalance)
        if len(self.imbalances) > MAX_IMBALANCES:
            del self.imbalances[0]
        return imbalance

    def get_significant_imbalances(
        self,
        asset: Optional[str] = None,
        threshold: float = DEFAULT_IMBALANCE_THRESHOLD,
        limit: int = 20,
    ) -> List[LiquidityImbalance]:
        result = [i for i in self.imbalances if i.ratio >= threshold]
        if asset:
            result = [i for i in result if i.asset == asset]
        return result[-limit:]

    def get_average_strength(self, asset: Optional[str] = None) -> float:
        items = self.imbalances
        if asset:
            items = [i for i in items if i.asset == asset]
        if not items:
            return 0.0
        return sum(i.strength for i in items) / len(items)
