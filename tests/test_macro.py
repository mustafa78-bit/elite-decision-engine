from datetime import datetime, timedelta, timezone

from macro.models import FearGreedIndex, MacroEvent, EconomicIndicator, VixDxySnapshot
from macro.analyzer import FearGreedAnalyzer, MacroEventAnalyzer, VixDxyPlaceholder
from macro.integration import MacroIntegration


class TestMacroModels:

    def test_fear_greed_defaults(self):
        fg = FearGreedIndex(value=50.0)
        assert fg.classification == "NEUTRAL"
        assert fg.source == "macro_module"

    def test_fear_greed_custom(self):
        fg = FearGreedIndex(value=80.0, classification="GREED")
        assert fg.classification == "GREED"

    def test_macro_event_defaults(self):
        me = MacroEvent(event_id="e1", event_type="CPI", asset="BTC")
        assert me.importance == "MEDIUM"
        assert me.confidence == 0.5
        assert me.source == "macro_module"

    def test_macro_event_custom(self):
        me = MacroEvent(
            event_id="e2", event_type="FED", asset="BTC",
            importance="HIGH", confidence=0.8,
        )
        assert me.importance == "HIGH"

    def test_economic_indicator_defaults(self):
        ei = EconomicIndicator(indicator_id="i1", name="CPI", value=3.2)
        assert ei.country == "US"
        assert ei.source == "macro_module"

    def test_vix_dxy_defaults(self):
        vs = VixDxySnapshot()
        assert vs.vix_value is None
        assert vs.dxy_value is None

    def test_vix_dxy_custom(self):
        vs = VixDxySnapshot(vix_value=25.5, dxy_value=104.3)
        assert vs.vix_value == 25.5
        assert vs.dxy_value == 104.3

    def test_serialization(self):
        fg = FearGreedIndex(value=75.0, classification="GREED")
        d = fg.to_dict()
        assert d["value"] == 75.0
        assert d["classification"] == "GREED"


class TestFearGreedAnalyzer:

    def test_classify_extreme_fear(self):
        fg = FearGreedAnalyzer()
        assert fg.classify(10) == "EXTREME_FEAR"
        assert fg.classify(25) == "EXTREME_FEAR"

    def test_classify_fear(self):
        fg = FearGreedAnalyzer()
        assert fg.classify(26) == "FEAR"
        assert fg.classify(45) == "FEAR"

    def test_classify_neutral(self):
        fg = FearGreedAnalyzer()
        assert fg.classify(50) == "NEUTRAL"
        assert fg.classify(55) == "NEUTRAL"

    def test_classify_greed(self):
        fg = FearGreedAnalyzer()
        assert fg.classify(56) == "GREED"
        assert fg.classify(75) == "GREED"

    def test_classify_extreme_greed(self):
        fg = FearGreedAnalyzer()
        assert fg.classify(76) == "EXTREME_GREED"
        assert fg.classify(100) == "EXTREME_GREED"

    def test_confidence_high(self):
        fg = FearGreedAnalyzer()
        conf = fg.calculate_confidence(10)
        assert conf > 0.7

    def test_confidence_low(self):
        fg = FearGreedAnalyzer()
        conf = fg.calculate_confidence(50)
        assert conf == 0.0

    def test_evaluate(self):
        fg = FearGreedAnalyzer()
        result = fg.evaluate(80)
        assert isinstance(result, FearGreedIndex)
        assert result.classification == "EXTREME_GREED"
        assert result.value == 80.0


class TestMacroEventAnalyzer:

    def test_process_event(self):
        analyzer = MacroEventAnalyzer()
        event = MacroEvent(event_id="e1", event_type="CPI", asset="BTC", importance="HIGH")
        result = analyzer.process_event(event)
        assert result.confidence > 0.5
        assert len(analyzer.events) == 1

    def test_get_upcoming(self):
        analyzer = MacroEventAnalyzer()
        analyzer.process_event(MacroEvent(event_id="e1", event_type="CPI", asset="BTC", importance="HIGH"))
        analyzer.process_event(MacroEvent(event_id="e2", event_type="JOBS", asset="ETH", importance="LOW"))
        upcoming = analyzer.get_upcoming(min_importance="MEDIUM")
        assert len(upcoming) == 1
        assert upcoming[0].event_id == "e1"

    def test_get_high_impact(self):
        analyzer = MacroEventAnalyzer()
        analyzer.process_event(MacroEvent(event_id="e1", event_type="CPI", asset="BTC", importance="HIGH"))
        analyzer.process_event(MacroEvent(event_id="e2", event_type="NEWS", asset="BTC", importance="LOW"))
        high = analyzer.get_high_impact()
        assert len(high) == 1

    def test_get_summary(self):
        analyzer = MacroEventAnalyzer()
        analyzer.process_event(MacroEvent(event_id="e1", event_type="CPI", asset="BTC", importance="HIGH"))
        summary = analyzer.get_summary()
        assert summary["total"] == 1
        assert summary["high_impact"] == 1

    def test_get_summary_empty(self):
        analyzer = MacroEventAnalyzer()
        summary = analyzer.get_summary()
        assert summary["total"] == 0

    def test_is_fresh(self):
        analyzer = MacroEventAnalyzer()
        event = MacroEvent(
            event_id="e1", event_type="CPI", asset="BTC",
            timestamp=datetime.now(timezone.utc),
        )
        assert analyzer.is_fresh(event) is True

    def test_is_fresh_old(self):
        analyzer = MacroEventAnalyzer()
        event = MacroEvent(
            event_id="e2", event_type="CPI", asset="BTC",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=100),
        )
        assert analyzer.is_fresh(event) is False


class TestVixDxyPlaceholder:

    def test_update_vix(self):
        vp = VixDxyPlaceholder()
        snap = vp.update(vix=25.5)
        assert snap.vix_value == 25.5

    def test_update_dxy(self):
        vp = VixDxyPlaceholder()
        snap = vp.update(dxy=104.3)
        assert snap.dxy_value == 104.3

    def test_update_both(self):
        vp = VixDxyPlaceholder()
        snap = vp.update(vix=25.5, dxy=104.3)
        assert snap.vix_value == 25.5
        assert snap.dxy_value == 104.3

    def test_get_latest_empty(self):
        vp = VixDxyPlaceholder()
        assert vp.get_latest() is None

    def test_get_latest_after_update(self):
        vp = VixDxyPlaceholder()
        vp.update(vix=20.0)
        latest = vp.get_latest()
        assert latest.vix_value == 20.0

    def test_get_summary_empty(self):
        vp = VixDxyPlaceholder()
        s = vp.get_summary()
        assert s["available"] is False

    def test_get_summary_with_data(self):
        vp = VixDxyPlaceholder()
        vp.update(vix=25.5, dxy=104.3)
        s = vp.get_summary()
        assert s["available"] is True
        assert s["vix"] == 25.5


class TestMacroIntegration:

    def test_enabled_default(self):
        mi = MacroIntegration()
        assert mi.enabled is True

    def test_process_fear_greed(self):
        mi = MacroIntegration()
        result = mi.process_fear_greed(80.0)
        assert isinstance(result, FearGreedIndex)
        assert result.classification == "EXTREME_GREED"

    def test_process_macro_event(self):
        mi = MacroIntegration()
        event = MacroEvent(event_id="e1", event_type="CPI", asset="BTC", importance="HIGH")
        result = mi.process_macro_event(event)
        assert result is not None
        assert len(mi.events) >= 1

    def test_process_macro_event_disabled(self):
        mi = MacroIntegration()
        mi.enabled = False
        event = MacroEvent(event_id="e1", event_type="CPI", asset="BTC")
        result = mi.process_macro_event(event)
        assert result is None

    def test_record_indicator(self):
        mi = MacroIntegration()
        ind = EconomicIndicator(indicator_id="i1", name="CPI", value=3.2)
        mi.record_indicator(ind)
        assert len(mi.indicators) == 1

    def test_update_vix_dxy(self):
        mi = MacroIntegration()
        snap = mi.update_vix_dxy(vix=25.0, dxy=105.0)
        assert snap.vix_value == 25.0
        assert snap.dxy_value == 105.0

    def test_get_features_enabled(self):
        mi = MacroIntegration()
        features = mi.get_features()
        assert features["macro_enabled"] is True
        assert "macro_features" in features

    def test_get_features_disabled(self):
        mi = MacroIntegration()
        mi.enabled = False
        features = mi.get_features()
        assert features["macro_enabled"] is False

    def test_get_features_tracks_events(self):
        mi = MacroIntegration()
        mi.process_macro_event(MacroEvent(event_id="e1", event_type="CPI", asset="BTC", importance="HIGH"))
        mi.process_macro_event(MacroEvent(event_id="e2", event_type="JOBS", asset="BTC", importance="LOW"))
        features = mi.get_features()
        mf = features["macro_features"]
        assert mf["total_events"] == 2
        assert mf["high_impact_events"] == 1

    def test_get_contribution_log(self):
        mi = MacroIntegration()
        mi.process_macro_event(MacroEvent(event_id="e1", event_type="CPI", asset="BTC"))
        log = mi.get_contribution_log()
        assert len(log) >= 1

    def test_evaluate_enabled(self):
        mi = MacroIntegration()
        result = mi.evaluate()
        assert result["ok"] is True
        assert result["macro_available"] is True

    def test_evaluate_disabled(self):
        mi = MacroIntegration()
        mi.enabled = False
        result = mi.evaluate()
        assert result["ok"] is True
        assert result["macro_available"] is False
