"""Tests for Decision Intelligence modules."""

from unittest.mock import MagicMock
import pandas as pd

from decision.aggregator import DecisionAggregator
from decision.confidence_v2 import ConfidenceEngineV2
from decision.explanation import ReasonBuilder, RiskExplanation, SignalExplanation
from decision.models import DecisionEvent, DecisionResult
from decision.timeline import DecisionTimeline
from market.models import Asset, AssetMetadata


class TestConfidenceEngineV2:

    def setup_method(self):
        self.engine = ConfidenceEngineV2()

    def test_evaluate_opportunity_with_scores(self):
        from scanner.models import Opportunity
        opp = Opportunity(
            symbol="BTCUSDT", side="LONG", strategy="trend",
            score=0.6, confidence=50.0, price=50000,
            probability_score=60.0, risk_score=0.3,
        )
        conf = self.engine.evaluate_opportunity(opp)
        assert 0 <= conf <= 100
        assert conf > 0

    def test_evaluate_opportunity_zero(self):
        from scanner.models import Opportunity
        opp = Opportunity(
            symbol="BTCUSDT", side="LONG", strategy="trend",
            score=0.0, confidence=0.0,
        )
        conf = self.engine.evaluate_opportunity(opp)
        assert conf >= 0

    def test_evaluate_asset_long_bullish(self):
        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            price=50000, ohlcv=df,
            indicators={"rsi": 50},
            features={"trend": "BULLISH", "momentum": "STRONG", "risk": "LOW",
                      "liquidity": "HIGH", "volatility_class": "NORMAL"},
        )
        conf = self.engine.evaluate_asset(asset, side="LONG")
        assert conf > 50

    def test_evaluate_asset_short_bearish(self):
        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            indicators={"rsi": 50},
            features={"trend": "BEARISH", "momentum": "STRONG", "risk": "LOW",
                      "liquidity": "HIGH", "volatility_class": "NORMAL"},
        )
        conf = self.engine.evaluate_asset(asset, side="SHORT")
        assert conf > 50

    def test_evaluate_asset_with_intelligence(self):
        from market.intelligence.models import IntelligenceBundle
        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        bundle = IntelligenceBundle(symbol="BTC", fear_greed={"value": 25, "label": "FEAR", "confidence": 0.8})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            ohlcv=df,
            indicators={"rsi": 50},
            features={"trend": "NEUTRAL", "momentum": "NEUTRAL", "risk": "MEDIUM",
                      "liquidity": "MEDIUM", "volatility_class": "NORMAL"},
            intelligence=bundle,
        )
        conf = self.engine.evaluate_asset(asset)
        assert conf > 0


class TestDecisionTimeline:

    def setup_method(self):
        self.timeline = DecisionTimeline()

    def test_record_and_get(self):
        self.timeline.record("BTC", "scan", "Scan complete", source="Scanner", details={"score": 0.8})
        events = self.timeline.get_events("BTC")
        assert len(events) == 1
        assert events[0].event_type == "scan"
        assert events[0].details["score"] == 0.8

    def test_get_events_empty_symbol(self):
        assert self.timeline.get_events("NONEXISTENT") == []

    def test_get_all_events(self):
        self.timeline.record("BTC", "a", "Event A")
        self.timeline.record("ETH", "b", "Event B")
        all_events = self.timeline.get_all_events()
        assert len(all_events) == 2

    def test_clear_symbol(self):
        self.timeline.record("BTC", "a", "Event A")
        self.timeline.record("ETH", "b", "Event B")
        self.timeline.clear("BTC")
        assert len(self.timeline.get_events("BTC")) == 0
        assert len(self.timeline.get_events("ETH")) == 1

    def test_clear_all(self):
        self.timeline.record("BTC", "a", "A")
        self.timeline.record("ETH", "b", "B")
        self.timeline.clear()
        assert len(self.timeline.get_all_events()) == 0

    def test_build_timeline(self):
        self.timeline.record("BTC", "scan", "Scan", source="Scanner")
        self.timeline.record("BTC", "conf", "Confidence", source="Engine")
        result = DecisionResult(symbol="BTC", side="LONG", decision="APPROVE")
        result = self.timeline.build_timeline(result)
        assert len(result.timeline) == 2


class TestReasonBuilder:

    def setup_method(self):
        self.builder = ReasonBuilder()

    def test_build_with_signals(self):
        from scanner.models import Opportunity
        opp = Opportunity(
            symbol="BTCUSDT", side="LONG", strategy="trend",
            score=0.8, confidence=80.0,
            signals=["BULLISH_TREND_ALIGNED", "RSI_BULLISH"],
        )
        reasons = self.builder.build(opp)
        assert len(reasons) >= 2
        assert any("EMA20" in r for r in reasons)

    def test_build_warnings(self):
        from scanner.models import Opportunity
        opp = Opportunity(
            symbol="BTCUSDT", side="LONG", strategy="trend",
            score=0.5, confidence=50.0,
            signals=["LOW_VOLUME_BREAKOUT"],
            risk_signals=["EXTREME_VOLATILITY_RISK"],
        )
        warnings = self.builder.build_warnings(opp)
        assert len(warnings) >= 2
        assert any("false" in w.lower() for w in warnings)

    def test_build_with_intelligence(self):
        from scanner.models import Opportunity
        from market.intelligence.models import IntelligenceBundle
        opp = Opportunity(
            symbol="BTCUSDT", side="LONG", strategy="trend",
            score=0.6, confidence=60.0,
        )
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            intelligence=IntelligenceBundle(
                symbol="BTC",
                fear_greed={"value": 30, "label": "FEAR", "confidence": 0.8},
                liquidity_context={"level": "HIGH", "score": 0.85},
            ),
        )
        reasons = self.builder.build(opp, asset)
        assert any("Fear" in r for r in reasons)
        assert any("liquidity" in r.lower() for r in reasons)


class TestSignalExplanation:

    def setup_method(self):
        self.explainer = SignalExplanation()

    def test_explain_known_signal(self):
        text = self.explainer.explain_signal("BULLISH_TREND_ALIGNED")
        assert "EMA20" in text

    def test_explain_unknown_signal(self):
        text = self.explainer.explain_signal("UNKNOWN_SIGNAL_XYZ")
        assert "UNKNOWN_SIGNAL_XYZ" in text

    def test_explain_multiple(self):
        texts = self.explainer.explain_signals(["BULLISH_TREND_ALIGNED", "HIGH_LIQUIDITY"])
        assert len(texts) == 2


class TestRiskExplanation:

    def setup_method(self):
        self.explainer = RiskExplanation()

    def test_high_risk(self):
        from scanner.models import Opportunity
        opp = Opportunity(
            symbol="BTC", side="LONG", strategy="trend",
            score=0.5, confidence=50.0,
            risk_signals=["EXTREME_VOLATILITY_RISK", "HIGH_ATR_RISK"],
        )
        text = self.explainer.explain(0.8, opp)
        assert "HIGH" in text
        assert "extreme" in text.lower()

    def test_low_risk(self):
        from scanner.models import Opportunity
        opp = Opportunity(
            symbol="BTC", side="LONG", strategy="trend",
            score=0.5, confidence=50.0,
            risk_signals=["LOW_VOLATILITY_BOOST", "HIGH_LIQUIDITY_BOOST"],
        )
        text = self.explainer.explain(0.2, opp)
        assert "LOW" in text
        assert "favorable" in text.lower()


class TestDecisionAggregator:

    def test_analyze_with_mocks(self):
        mock_scanner = MagicMock()
        mock_market = MagicMock()
        mock_confidence = MagicMock()
        mock_timeline = MagicMock()
        mock_reason = MagicMock()
        mock_risk = MagicMock()

        from scanner.models import Opportunity
        mock_opp = Opportunity(
            symbol="BTCUSDT", side="LONG", strategy="trend",
            score=0.75, confidence=70.0,
            probability_score=65.0, risk_score=0.35,
            signals=["BULLISH_TREND_ALIGNED"],
            probability_signals=["STRONG_TREND_BOOST"],
            risk_signals=[],
        )
        mock_scanner.scan.return_value = [mock_opp]
        mock_confidence.evaluate_opportunity.return_value = 85.0
        mock_reason.build.return_value = ["Strong trend alignment"]
        mock_reason.build_warnings.return_value = []
        mock_timeline.build_timeline.side_effect = lambda r: r

        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        asset = Asset(
            symbol="BTCUSDT", metadata=AssetMetadata(symbol="BTCUSDT"),
            price=50000, ohlcv=df,
            indicators={"rsi": 55},
            features={"trend": "BULLISH"},
            context={"btc": {"btc_trend": "BULLISH"}, "session": "NY", "funding": {"state": "NEUTRAL"}},
        )
        mock_market.get_asset.return_value = asset

        aggregator = DecisionAggregator(
            scanner=mock_scanner,
            market_service=mock_market,
            confidence_engine=mock_confidence,
            timeline=mock_timeline,
            reason_builder=mock_reason,
            risk_explanation=mock_risk,
        )

        result = aggregator.analyze("BTCUSDT")
        assert result is not None
        assert result.decision == "STRONG_APPROVE"
        assert result.symbol == "BTCUSDT"

    def test_analyze_empty_asset(self):
        mock_market = MagicMock()
        empty = Asset(symbol="BTC", metadata=AssetMetadata(symbol="BTC"))
        mock_market.get_asset.return_value = empty
        agg = DecisionAggregator(market_service=mock_market)
        result = agg.analyze("BTC")
        assert result is None

    def test_analyze_no_opportunities(self):
        mock_scanner = MagicMock()
        mock_market = MagicMock()
        mock_scanner.scan.return_value = []

        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        asset = Asset(
            symbol="BTCUSDT", metadata=AssetMetadata(symbol="BTCUSDT"),
            price=50000, ohlcv=df,
            indicators={}, features={},
        )
        mock_market.get_asset.return_value = asset

        agg = DecisionAggregator(scanner=mock_scanner, market_service=mock_market)
        result = agg.analyze("BTCUSDT")
        assert result is None

    def test_analyze_multiple(self):
        mock_scanner = MagicMock()
        mock_market = MagicMock()

        from scanner.models import Opportunity
        mock_scanner.scan.return_value = [
            Opportunity(symbol="BTCUSDT", side="LONG", strategy="trend", score=0.7, confidence=70.0),
        ]

        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        asset = Asset(
            symbol="BTCUSDT", metadata=AssetMetadata(symbol="BTCUSDT"),
            price=50000, ohlcv=df,
            indicators={"rsi": 55},
            features={"trend": "BULLISH"},
            context={"btc": {"btc_trend": "BULLISH"}, "session": "NY", "funding": {"state": "NEUTRAL"}},
        )
        mock_market.get_asset.return_value = asset

        agg = DecisionAggregator(scanner=mock_scanner, market_service=mock_market)
        results = agg.analyze_multiple(["BTCUSDT", "ETHUSDT"], top_n=5)
        assert len(results) >= 1
