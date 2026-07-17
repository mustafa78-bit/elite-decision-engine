from datetime import datetime, timezone

from liquidity.models import (
    LiquidityZone,
    LiquiditySweep,
    LiquidityImbalance,
    LiquidityEvent,
)
from liquidity.analyzer import ZoneManager, SweepDetector, ImbalanceAnalyzer
from liquidity.integration import LiquidityIntegration


class TestLiquidityModels:

    def test_liquidity_zone_defaults(self):
        zone = LiquidityZone(
            zone_id="z1", asset="BTC", zone_type="SUPPORT",
            price_low=50000.0, price_high=51000.0,
        )
        assert zone.strength == 0.5
        assert zone.touches == 0
        assert zone.is_active is True
        assert zone.source == "liquidity_module"

    def test_liquidity_zone_custom(self):
        now = datetime.now(timezone.utc)
        zone = LiquidityZone(
            zone_id="z2", asset="ETH", zone_type="RESISTANCE",
            price_low=3000.0, price_high=3100.0,
            strength=0.8, touches=5, is_active=False,
            last_tested=now,
        )
        assert zone.strength == 0.8
        assert zone.touches == 5
        assert zone.is_active is False
        assert zone.last_tested == now

    def test_liquidity_sweep_defaults(self):
        sweep = LiquiditySweep(
            sweep_id="s1", asset="BTC", zone_id="z1",
            direction="BULLISH", price=52000.0, volume=100.0,
        )
        assert sweep.confidence == 0.5
        assert sweep.source == "liquidity_module"

    def test_liquidity_imbalance_defaults(self):
        imb = LiquidityImbalance(
            asset="BTC", bid_volume=1000.0, ask_volume=800.0,
        )
        assert imb.ratio == 1.0
        assert imb.direction == "NEUTRAL"
        assert imb.strength == 0.0

    def test_liquidity_event_defaults(self):
        event = LiquidityEvent(
            event_id="e1", event_type="ZONE_TOUCH",
            asset="BTC", price=50500.0,
        )
        assert event.confidence == 0.5
        assert event.source == "liquidity_module"

    def test_serializable_mixin_to_dict(self):
        zone = LiquidityZone(
            zone_id="z1", asset="BTC", zone_type="SUPPORT",
            price_low=50000.0, price_high=51000.0,
        )
        d = zone.to_dict()
        assert d["zone_id"] == "z1"
        assert d["asset"] == "BTC"
        assert d["price_low"] == 50000.0
        assert isinstance(d["formed_at"], str)


class TestZoneManager:

    def test_create_zone(self):
        zm = ZoneManager()
        zone = zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        assert zone.asset == "BTC"
        assert zone.zone_type == "SUPPORT"
        assert zone.price_low == 50000.0
        assert zone.price_high == 51000.0

    def test_create_zone_swaps_low_high(self):
        zm = ZoneManager()
        zone = zm.create_zone("ETH", "RESISTANCE", 3100.0, 3000.0)
        assert zone.price_low == 3000.0
        assert zone.price_high == 3100.0

    def test_test_zone_within_threshold(self):
        zm = ZoneManager()
        zone = zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        assert zm.test_zone(zone.zone_id, 50500.0) is True

    def test_test_zone_far_away(self):
        zm = ZoneManager()
        zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        assert zm.test_zone("zone_BTC_0_", 60000.0) is False

    def test_test_zone_inactive(self):
        zm = ZoneManager()
        zone = zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        zm.deactivate_zone(zone.zone_id)
        assert zm.test_zone(zone.zone_id, 50500.0) is False

    def test_test_zone_nonexistent(self):
        zm = ZoneManager()
        assert zm.test_zone("nonexistent", 50000.0) is False

    def test_touch_zone(self):
        zm = ZoneManager()
        zone = zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        event = zm.touch_zone(zone.zone_id, 50500.0)
        assert event is not None
        assert event.event_type == "ZONE_TOUCH"
        assert zm.zones[zone.zone_id].touches == 1

    def test_touch_zone_outside(self):
        zm = ZoneManager()
        zone = zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        event = zm.touch_zone(zone.zone_id, 60000.0)
        assert event is None

    def test_deactivate_zone(self):
        zm = ZoneManager()
        zone = zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        assert zm.deactivate_zone(zone.zone_id) is True
        assert zm.zones[zone.zone_id].is_active is False

    def test_deactivate_nonexistent(self):
        zm = ZoneManager()
        assert zm.deactivate_zone("ghost") is False

    def test_get_active_zones(self):
        zm = ZoneManager()
        zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        zm.create_zone("ETH", "RESISTANCE", 3000.0, 3100.0)
        assert len(zm.get_active_zones()) == 2
        assert len(zm.get_active_zones("BTC")) == 1

    def test_get_zone_summary(self):
        zm = ZoneManager()
        zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        zm.create_zone("ETH", "RESISTANCE", 3000.0, 3100.0)
        summary = zm.get_zone_summary()
        assert summary["total"] >= 2


class TestSweepDetector:

    def test_detect_sweep_bullish(self):
        zm = ZoneManager()
        sd = SweepDetector(zm)
        zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        sweep = sd.detect_sweep("BTC", 52000.0, 100.0, "BULLISH")
        assert sweep is not None
        assert sweep.direction == "BULLISH"

    def test_detect_sweep_bearish(self):
        zm = ZoneManager()
        sd = SweepDetector(zm)
        zm.create_zone("BTC", "RESISTANCE", 50000.0, 51000.0)
        sweep = sd.detect_sweep("BTC", 49000.0, 100.0, "BEARISH")
        assert sweep is not None
        assert sweep.direction == "BEARISH"

    def test_detect_sweep_no_match(self):
        zm = ZoneManager()
        sd = SweepDetector(zm)
        zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        sweep = sd.detect_sweep("BTC", 50500.0, 100.0, "BULLISH")
        assert sweep is None

    def test_detect_sweep_deactivates_zone(self):
        zm = ZoneManager()
        sd = SweepDetector(zm)
        zone = zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        sd.detect_sweep("BTC", 52000.0, 100.0, "BULLISH")
        assert zm.zones[zone.zone_id].is_active is False

    def test_get_recent_sweeps(self):
        zm = ZoneManager()
        sd = SweepDetector(zm)
        zm.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        sd.detect_sweep("BTC", 52000.0, 100.0, "BULLISH")
        assert len(sd.get_recent_sweeps()) == 1
        assert len(sd.get_recent_sweeps("ETH")) == 0


class TestImbalanceAnalyzer:

    def test_calculate_imbalance_bullish(self):
        ia = ImbalanceAnalyzer()
        imb = ia.calculate_imbalance("BTC", 2000.0, 1000.0)
        assert imb.direction == "BULLISH"
        assert imb.ratio >= 2.0

    def test_calculate_imbalance_bearish(self):
        ia = ImbalanceAnalyzer()
        imb = ia.calculate_imbalance("BTC", 1000.0, 2000.0)
        assert imb.direction == "BEARISH"
        assert imb.ratio >= 2.0

    def test_calculate_imbalance_neutral(self):
        ia = ImbalanceAnalyzer()
        imb = ia.calculate_imbalance("BTC", 1000.0, 1000.0)
        assert imb.direction == "NEUTRAL"
        assert imb.ratio == 1.0

    def test_calculate_imbalance_zero_values(self):
        ia = ImbalanceAnalyzer()
        imb = ia.calculate_imbalance("BTC", 0.0, 0.0)
        assert imb.direction == "NEUTRAL"

    def test_get_significant_imbalances(self):
        ia = ImbalanceAnalyzer()
        ia.calculate_imbalance("BTC", 1000.0, 1000.0)
        ia.calculate_imbalance("ETH", 3000.0, 1000.0)
        sig = ia.get_significant_imbalances(threshold=2.0)
        assert len(sig) == 1

    def test_get_average_strength(self):
        ia = ImbalanceAnalyzer()
        ia.calculate_imbalance("BTC", 2000.0, 1000.0)
        ia.calculate_imbalance("BTC", 1000.0, 2000.0)
        avg = ia.get_average_strength("BTC")
        assert avg > 0.0


class TestLiquidityIntegration:

    def test_enabled_default(self):
        li = LiquidityIntegration()
        assert li.enabled is True

    def test_get_features_enabled(self):
        li = LiquidityIntegration()
        features = li.get_features()
        assert features["liquidity_enabled"] is True
        assert "liquidity_features" in features

    def test_get_features_disabled(self):
        li = LiquidityIntegration()
        li.enabled = False
        features = li.get_features()
        assert features["liquidity_enabled"] is False

    def test_get_contribution_log(self):
        li = LiquidityIntegration()
        event = LiquidityEvent(
            event_id="e1", event_type="ZONE_TOUCH",
            asset="BTC", price=50000.0,
        )
        li.add_event(event)
        log = li.get_contribution_log()
        assert len(log) == 1
        assert log[0]["event_id"] == "e1"

    def test_evaluate_enabled(self):
        li = LiquidityIntegration()
        result = li.evaluate()
        assert result["ok"] is True
        assert result["liquidity_available"] is True

    def test_evaluate_disabled(self):
        li = LiquidityIntegration()
        li.enabled = False
        result = li.evaluate()
        assert result["liquidity_available"] is False

    def test_zone_and_sweep_integration(self):
        li = LiquidityIntegration()
        zone = li.zone_manager.create_zone("BTC", "SUPPORT", 50000.0, 51000.0)
        sweep = li.sweep_detector.detect_sweep("BTC", 52000.0, 100.0, "BULLISH")
        assert sweep is not None
        features = li.get_features()
        assert features["liquidity_features"]["active_zone_count"] == 0
        assert features["liquidity_features"]["recent_sweep_count"] == 1
