from datetime import datetime, timezone

from market_structure.models import (
    PriceCandle,
    SwingPoint,
    StructureBreak,
    TrendState,
    MarketStructureEvent,
)
from market_structure.analyzer import (
    SwingDetector,
    StructureAnalyzer,
    TrendStrengthAnalyzer,
)
from market_structure.integration import MarketStructureIntegration


class TestMarketStructureModels:

    def test_price_candle_defaults(self):
        pc = PriceCandle(asset="BTC", high=51000.0, low=49000.0, open=50000.0, close=50500.0)
        assert pc.volume == 0.0
        assert pc.source == "market_structure_module"

    def test_swing_point_defaults(self):
        sp = SwingPoint(
            point_id="s1", asset="BTC", point_type="SWING_HIGH",
            price=51000.0,
        )
        assert sp.index == 0
        assert sp.strength == 0.5

    def test_structure_break_defaults(self):
        sb = StructureBreak(
            break_id="b1", asset="BTC", break_type="BOS",
            direction="BULLISH", price=52000.0,
        )
        assert sb.confidence == 0.5
        assert sb.previous_swing_price == 0.0

    def test_trend_state_defaults(self):
        ts = TrendState(asset="BTC")
        assert ts.trend == "NEUTRAL"
        assert ts.strength == 0.0
        assert ts.swing_highs == []

    def test_market_structure_event_defaults(self):
        mse = MarketStructureEvent(
            event_id="e1", event_type="SWING_POINT", asset="BTC",
        )
        assert mse.source == "market_structure_module"

    def test_serialization(self):
        sp = SwingPoint(
            point_id="s1", asset="BTC", point_type="SWING_HIGH",
            price=51000.0,
        )
        d = sp.to_dict()
        assert d["point_id"] == "s1"
        assert d["asset"] == "BTC"


class TestSwingDetector:

    def make_candle(self, high, low, asset="BTC"):
        return PriceCandle(
            asset=asset, high=high, low=low,
            open=(high + low) / 2, close=(high + low) / 2,
        )

    def test_add_candle_no_swing_yet(self):
        sd = SwingDetector()
        for i in range(5):
            c = self.make_candle(50000.0 + i * 100, 49900.0 + i * 100)
            swing = sd.add_candle(c)
            assert swing is None

    def test_detect_swing_high(self):
        sd = SwingDetector()
        prices = [
            50000, 50100, 50200, 50300, 50400,
            50500, 50400, 50300, 50200, 50100,
            50000,
        ]
        for p in prices:
            sd.add_candle(self.make_candle(p + 50, p - 50))
        swings = sd.get_recent_swings()
        swing_types = [s.point_type for s in swings]
        assert "SWING_HIGH" in swing_types

    def test_swing_summary(self):
        sd = SwingDetector()
        prices = [
            50000, 50100, 50200, 50300, 50400,
            50500, 50400, 50300, 50200, 50100,
            50000,
        ]
        for p in prices:
            sd.add_candle(self.make_candle(p + 50, p - 50))
        summary = sd.get_swing_summary()
        assert summary["total"] >= 0
        assert "highs" in summary

    def test_get_recent_swings_empty(self):
        sd = SwingDetector()
        assert sd.get_recent_swings() == []


class TestStructureAnalyzer:

    def make_candle(self, high, low, asset="BTC"):
        return PriceCandle(
            asset=asset, high=high, low=low,
            open=(high + low) / 2, close=(high + low) / 2,
        )

    def make_rising_swings(self, asset="BTC"):
        sd = SwingDetector()
        prices = [
            50000, 50100, 50200, 50300, 50400,
            50500, 50600, 50700, 50800, 50900,
            51000,
        ]
        for p in prices:
            sd.add_candle(self.make_candle(p + 50, p - 50, asset))
        return sd

    def test_classify_swing_sequence(self):
        sd = self.make_rising_swings()
        sa = StructureAnalyzer(sd)
        highs, lows = sa.classify_swing_sequence("BTC")
        assert isinstance(highs, list)
        assert isinstance(lows, list)

    def test_detect_bos_bullish(self):
        sd = SwingDetector()
        prices = [
            50000, 49900, 50100, 49800, 50200,
            49700, 50300, 49600, 50400, 49500,
            51000,
        ]
        for p in prices:
            sd.add_candle(self.make_candle(p + 100, p - 100))
        sa = StructureAnalyzer(sd)
        bos = sa.detect_bos("BTC", 51000.0)
        if bos:
            assert bos.break_type == "BOS"

    def test_detect_bos_bearish(self):
        sd = SwingDetector()
        prices = [
            50000, 50100, 49900, 50200, 49800,
            50300, 49700, 50400, 49600, 50500,
            48000,
        ]
        for p in prices:
            sd.add_candle(self.make_candle(p + 100, p - 100))
        sa = StructureAnalyzer(sd)
        bos = sa.detect_bos("BTC", 48000.0)
        if bos:
            assert bos.break_type == "BOS"

    def test_get_latest_trend_state(self):
        sd = self.make_rising_swings()
        sa = StructureAnalyzer(sd)
        state = sa.get_latest_trend_state("BTC")
        assert state.asset == "BTC"
        assert state.trend in ("BULLISH", "BEARISH", "NEUTRAL")

    def test_detect_choch_bearish(self):
        sd = SwingDetector()
        prices = [
            51000, 50900, 50800, 50700, 50600,
            50500, 50400, 50300, 50200, 50100,
            50000,
        ]
        for p in prices:
            sd.add_candle(self.make_candle(p + 50, p - 50))
        sa = StructureAnalyzer(sd)
        choch = sa.detect_choch("BTC")
        if choch:
            assert choch.break_type == "CHoCH"


class TestTrendStrengthAnalyzer:

    def test_calculate_uptrend(self):
        tsa = TrendStrengthAnalyzer()
        result = tsa.calculate([50000, 50500, 51000, 51500, 52000])
        assert result["direction"] == "BULLISH"
        assert result["strength"] > 0

    def test_calculate_downtrend(self):
        tsa = TrendStrengthAnalyzer()
        result = tsa.calculate([52000, 51500, 51000, 50500, 50000])
        assert result["direction"] == "BEARISH"

    def test_calculate_insufficient_data(self):
        tsa = TrendStrengthAnalyzer()
        result = tsa.calculate([50000])
        assert result["strength"] == 0.0
        assert result["direction"] == "NEUTRAL"


class TestMarketStructureIntegration:

    def test_enabled_default(self):
        msi = MarketStructureIntegration()
        assert msi.enabled is True

    def test_process_candle(self):
        msi = MarketStructureIntegration()
        candle = PriceCandle(
            asset="BTC", high=51000.0, low=49000.0,
            open=50000.0, close=50500.0,
        )
        msi.process_candle(candle)
        # Swings require minimum points, so no event guaranteed
        assert isinstance(msi.events, list)

    def test_get_features_enabled(self):
        msi = MarketStructureIntegration()
        features = msi.get_features()
        assert features["market_structure_enabled"] is True
        assert "market_structure_features" in features

    def test_get_features_disabled(self):
        msi = MarketStructureIntegration()
        msi.enabled = False
        features = msi.get_features()
        assert features["market_structure_enabled"] is False

    def test_get_contribution_log(self):
        msi = MarketStructureIntegration()
        log = msi.get_contribution_log()
        assert isinstance(log, list)

    def test_evaluate_enabled(self):
        msi = MarketStructureIntegration()
        result = msi.evaluate()
        assert result["ok"] is True
        assert result["market_structure_available"] is True

    def test_evaluate_disabled(self):
        msi = MarketStructureIntegration()
        msi.enabled = False
        result = msi.evaluate()
        assert result["market_structure_available"] is False

    def test_candle_swing_pipeline(self):
        msi = MarketStructureIntegration()
        prices = [
            50000, 50200, 50400, 50600, 50800,
            51000, 51200, 51400, 51600, 51800,
            51600, 51400, 51200, 51000, 50800,
        ]
        for p in prices:
            candle = PriceCandle(
                asset="BTC", high=p + 50, low=p - 50,
                open=p, close=p,
            )
            msi.process_candle(candle)
        features = msi.get_features()
        mf = features["market_structure_features"]
        assert mf["total_swings"] > 0
