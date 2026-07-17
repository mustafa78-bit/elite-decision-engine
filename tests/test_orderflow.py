from datetime import datetime, timezone

from orderflow.models import (
    Trade,
    DeltaPoint,
    VolumeImbalance,
    CVD,
    AggressiveOrder,
    OrderFlowEvent,
)
from orderflow.analyzer import (
    DeltaTracker,
    CVDAnalyzer,
    AggressiveOrderDetector,
    VolumeImbalanceAnalyzer,
)
from orderflow.integration import OrderFlowIntegration


class TestOrderFlowModels:

    def test_trade_defaults(self):
        t = Trade(trade_id="t1", asset="BTC", side="BUY", size=1.0, price=50000.0)
        assert t.is_aggressive is False
        assert t.source == "orderflow_module"

    def test_delta_point_defaults(self):
        dp = DeltaPoint(asset="BTC")
        assert dp.buy_volume == 0.0
        assert dp.delta == 0.0
        assert dp.cumulative_delta == 0.0

    def test_volume_imbalance_defaults(self):
        vi = VolumeImbalance(asset="BTC", buy_volume=100.0, sell_volume=50.0)
        assert vi.timeframe == "1m"
        assert vi.direction == "NEUTRAL"

    def test_cvd_defaults(self):
        cvd = CVD(asset="BTC")
        assert cvd.value == 0.0
        assert cvd.trend == "NEUTRAL"
        assert cvd.divergence is None

    def test_aggressive_order_defaults(self):
        ao = AggressiveOrder(
            order_id="a1", asset="BTC", side="BUY",
            size=1.0, price=50000.0,
        )
        assert ao.is_aggressive is True
        assert ao.confidence == 0.5

    def test_orderflow_event_defaults(self):
        oe = OrderFlowEvent(
            event_id="e1", event_type="AGGRESSIVE_TRADE",
            asset="BTC",
        )
        assert oe.source == "orderflow_module"
        assert oe.confidence == 0.5

    def test_serialization(self):
        dp = DeltaPoint(asset="BTC", buy_volume=100.0, delta=50.0)
        d = dp.to_dict()
        assert d["asset"] == "BTC"
        assert d["buy_volume"] == 100.0


class TestDeltaTracker:

    def test_record_buy_trade(self):
        dt = DeltaTracker()
        trade = Trade(trade_id="t1", asset="BTC", side="BUY", size=1.0, price=50100.0)
        point = dt.record_trade(trade, 50000.0)
        assert point.delta == 1.0
        assert point.buy_volume == 1.0

    def test_record_sell_trade(self):
        dt = DeltaTracker()
        trade = Trade(trade_id="t2", asset="BTC", side="SELL", size=2.0, price=49900.0)
        point = dt.record_trade(trade, 50000.0)
        assert point.delta == -2.0
        assert point.sell_volume == 2.0

    def test_cumulative_delta(self):
        dt = DeltaTracker()
        dt.record_trade(Trade("t1", "BTC", "BUY", 1.0, 50100.0), 50000.0)
        dt.record_trade(Trade("t2", "BTC", "SELL", 0.5, 49900.0), 50000.0)
        assert dt.get_cumulative_delta() == 0.5

    def test_get_current_delta_empty(self):
        dt = DeltaTracker()
        assert dt.get_current_delta() == 0.0

    def test_get_delta_trend(self):
        dt = DeltaTracker()
        for i in range(5):
            dt.record_trade(Trade(f"t{i}", "BTC", "BUY", 1.0, 50100.0), 50000.0)
        assert dt.get_delta_trend() == "POSITIVE"

    def test_get_delta_summary(self):
        dt = DeltaTracker()
        dt.record_trade(Trade("t1", "BTC", "BUY", 1.0, 50100.0), 50000.0)
        summary = dt.get_delta_summary()
        assert "current_delta" in summary
        assert "cumulative_delta" in summary
        assert "trend" in summary


class TestCVDAnalyzer:

    def test_update_increases_cvd(self):
        cvd = CVDAnalyzer()
        point = cvd.update("BTC", 10.0)
        assert point.value > 0

    def test_update_decreases_cvd(self):
        cvd = CVDAnalyzer()
        cvd.update("BTC", 10.0)
        point = cvd.update("BTC", -5.0)
        assert point.value == 5.0

    def test_get_cvd_value(self):
        cvd = CVDAnalyzer()
        assert cvd.get_cvd_value() == 0.0
        cvd.update("BTC", 15.0)
        assert cvd.get_cvd_value() == 15.0

    def test_get_cvd_trend_default(self):
        cvd = CVDAnalyzer()
        assert cvd.get_cvd_trend() == "NEUTRAL"


class TestAggressiveOrderDetector:

    def test_classify_buy_aggressive(self):
        ad = AggressiveOrderDetector()
        trade = Trade("t1", "BTC", "BUY", 1.0, 50100.0)
        agg = ad.classify_trade(trade, 50000.0)
        assert agg.is_aggressive is True

    def test_classify_sell_aggressive(self):
        ad = AggressiveOrderDetector()
        trade = Trade("t2", "BTC", "SELL", 1.0, 49900.0)
        agg = ad.classify_trade(trade, 50000.0)
        assert agg.is_aggressive is True

    def test_classify_non_aggressive(self):
        ad = AggressiveOrderDetector()
        trade = Trade("t3", "BTC", "BUY", 1.0, 49900.0)
        agg = ad.classify_trade(trade, 50000.0)
        assert agg.is_aggressive is False

    def test_get_aggressive_ratio(self):
        ad = AggressiveOrderDetector()
        for i in range(5):
            trade = Trade(f"t{i}", "BTC", "BUY", 1.0, 50100.0)
            ad.classify_trade(trade, 50000.0)
        for i in range(3):
            trade = Trade(f"ts{i}", "BTC", "SELL", 1.0, 49900.0)
            ad.classify_trade(trade, 50000.0)
        ratio = ad.get_aggressive_ratio()
        assert ratio["total"] >= 8

    def test_get_aggressive_ratio_empty(self):
        ad = AggressiveOrderDetector()
        ratio = ad.get_aggressive_ratio()
        assert ratio["ratio"] == 0.0


class TestVolumeImbalanceAnalyzer:

    def test_calculate_bullish(self):
        via = VolumeImbalanceAnalyzer()
        imb = via.calculate("BTC", 2000.0, 1000.0)
        assert imb.direction == "BULLISH"

    def test_calculate_bearish(self):
        via = VolumeImbalanceAnalyzer()
        imb = via.calculate("BTC", 1000.0, 2000.0)
        assert imb.direction == "BEARISH"

    def test_calculate_neutral(self):
        via = VolumeImbalanceAnalyzer()
        imb = via.calculate("BTC", 1000.0, 1000.0)
        assert imb.direction == "NEUTRAL"

    def test_get_significant(self):
        via = VolumeImbalanceAnalyzer()
        via.calculate("BTC", 1000.0, 1000.0)
        via.calculate("ETH", 5000.0, 1000.0)
        sig = via.get_significant(threshold=3.0)
        assert len(sig) == 1

    def test_get_summary(self):
        via = VolumeImbalanceAnalyzer()
        via.calculate("BTC", 2000.0, 1000.0)
        summary = via.get_summary("BTC")
        assert summary["total"] == 1


class TestOrderFlowIntegration:

    def test_enabled_default(self):
        ofi = OrderFlowIntegration()
        assert ofi.enabled is True

    def test_process_trade_tracks_delta(self):
        ofi = OrderFlowIntegration()
        trade = Trade("t1", "BTC", "BUY", 1.0, 50100.0)
        ofi.process_trade(trade, 50000.0)
        assert ofi.delta_tracker.get_cumulative_delta() == 1.0

    def test_process_trade_tracks_cvd(self):
        ofi = OrderFlowIntegration()
        trade = Trade("t1", "BTC", "BUY", 1.0, 50100.0)
        ofi.process_trade(trade, 50000.0)
        assert ofi.cvd_analyzer.get_cvd_value() > 0

    def test_get_features_enabled(self):
        ofi = OrderFlowIntegration()
        features = ofi.get_features()
        assert features["orderflow_enabled"] is True
        assert "orderflow_features" in features

    def test_get_features_disabled(self):
        ofi = OrderFlowIntegration()
        ofi.enabled = False
        features = ofi.get_features()
        assert features["orderflow_enabled"] is False

    def test_get_contribution_log(self):
        ofi = OrderFlowIntegration()
        trade = Trade("t1", "BTC", "BUY", 1.0, 50100.0)
        ofi.process_trade(trade, 50000.0)
        log = ofi.get_contribution_log()
        assert len(log) >= 1

    def test_evaluate_enabled(self):
        ofi = OrderFlowIntegration()
        result = ofi.evaluate()
        assert result["ok"] is True
        assert result["orderflow_available"] is True

    def test_evaluate_disabled(self):
        ofi = OrderFlowIntegration()
        ofi.enabled = False
        result = ofi.evaluate()
        assert result["orderflow_available"] is False

    def test_disabled_process_trade_does_nothing(self):
        ofi = OrderFlowIntegration()
        ofi.enabled = False
        trade = Trade("t1", "BTC", "BUY", 1.0, 50100.0)
        ofi.process_trade(trade, 50000.0)
        assert ofi.delta_tracker.get_cumulative_delta() == 0.0
