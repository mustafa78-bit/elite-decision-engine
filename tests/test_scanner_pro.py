"""Tests for Elite Scanner PRO modules."""

from unittest.mock import MagicMock

import pandas as pd

from scanner.confidence import ConfidenceScorer
from scanner.dto import ScannerDashboardDTO, opportunity_to_dto
from scanner.filters import FalseSignalFilter, MarketFilter
from scanner.models import Opportunity, ScanResult
from scanner.probability import ProbabilityEngine
from scanner.risk import RiskScorer
from scanner.watchlist import WatchlistEngine


class TestProbabilityEngine:

    def setup_method(self):
        self.engine = ProbabilityEngine()

    def test_basic_probability(self):
        prob, signals = self.engine.estimate(composite_score=0.5)
        assert 0 < prob < 100
        assert prob > 0

    def test_btc_bullish_boost(self):
        prob_neutral, _ = self.engine.estimate(composite_score=0.5)
        prob_bullish, _ = self.engine.estimate(composite_score=0.5, btc_trend="BULLISH")
        assert prob_bullish > prob_neutral

    def test_btc_bearish_penalty(self):
        prob_neutral, _ = self.engine.estimate(composite_score=0.5)
        prob_bearish, _ = self.engine.estimate(composite_score=0.5, btc_trend="BEARISH")
        assert prob_bearish < prob_neutral

    def test_fear_buying_opportunity(self):
        prob, signals = self.engine.estimate(composite_score=0.5, fear_greed_value=30)
        assert "FEAR_BUYING_OPPORTUNITY" in signals

    def test_extreme_greed_caution(self):
        prob, signals = self.engine.estimate(composite_score=0.5, fear_greed_value=85)
        assert "EXTREME_GREED_CAUTION" in signals

    def test_high_funding_long_penalty(self):
        prob, signals = self.engine.estimate(composite_score=0.5, funding_level="HIGH_LONG")
        assert "HIGH_FUNDING_LONG_PENALTY" in signals

    def test_probability_bounds(self):
        prob, _ = self.engine.estimate(composite_score=2.0, trend_score=1.0, breakout_score=1.0,
                                        liquidity_score=1.0, btc_trend="BULLISH")
        assert prob <= 100
        prob2, _ = self.engine.estimate(composite_score=0.0)
        assert prob2 >= 0

    def test_short_probability_btc_bearish_boost(self):
        prob_neutral, _ = self.engine.estimate(composite_score=0.5, side="SHORT")
        prob_bearish, _ = self.engine.estimate(composite_score=0.5, btc_trend="BEARISH", side="SHORT")
        assert prob_bearish > prob_neutral

    def test_short_probability_btc_bullish_penalty(self):
        prob_neutral, _ = self.engine.estimate(composite_score=0.5, side="SHORT")
        prob_bullish, _ = self.engine.estimate(composite_score=0.5, btc_trend="BULLISH", side="SHORT")
        assert prob_bullish < prob_neutral

    def test_short_probability_greed_shorting_opportunity(self):
        prob, signals = self.engine.estimate(composite_score=0.5, fear_greed_value=70, side="SHORT")
        assert "GREED_SHORTING_OPPORTUNITY" in signals

    def test_short_probability_extreme_greed_opportunity(self):
        prob, signals = self.engine.estimate(composite_score=0.5, fear_greed_value=90, side="SHORT")
        assert "EXTREME_GREED_OPPORTUNITY" in signals

    def test_short_probability_funding_long_edge(self):
        prob, signals = self.engine.estimate(composite_score=0.5, funding_level="HIGH_LONG", side="SHORT")
        assert "HIGH_FUNDING_LONG_EDGE" in signals


class TestRiskScorer:

    def setup_method(self):
        self.scorer = RiskScorer()

    def test_extreme_volatility_risk(self):
        risk, signals = self.scorer.score(volatility_class="EXTREME")
        assert risk > 0.3
        assert "EXTREME_VOLATILITY_RISK" in signals

    def test_low_volatility_boost(self):
        risk, signals = self.scorer.score(volatility_class="LOW")
        assert risk < 0.3

    def test_high_atr_risk(self):
        risk, signals = self.scorer.score(volatility_class="NORMAL", atr_pct=6.0)
        assert "HIGH_ATR_RISK" in signals

    def test_low_liquidity_risk(self):
        risk, signals = self.scorer.score(liquidity_score=0.2)
        assert "LOW_LIQUIDITY_RISK" in signals

    def test_high_liquidity_boost(self):
        risk, signals = self.scorer.score(liquidity_score=0.8)
        assert "HIGH_LIQUIDITY_BOOST" in signals

    def test_risk_bounds(self):
        risk, _ = self.scorer.score(volatility_class="EXTREME", risk_feature="HIGH", atr_pct=10.0)
        assert 0 <= risk <= 1


class TestConfidenceScorer:

    def setup_method(self):
        self.scorer = ConfidenceScorer()

    def test_no_probability(self):
        conf, signals = self.scorer.compute(probability=0)
        assert conf == 0
        assert "NO_PROBABILITY" in signals

    def test_high_probability_confidence(self):
        conf, _ = self.scorer.compute(probability=80, risk_score=0.2, signal_count=8)
        assert conf > 50

    def test_high_risk_reduces_confidence(self):
        conf_low_risk, _ = self.scorer.compute(probability=50, risk_score=0.1)
        conf_high_risk, _ = self.scorer.compute(probability=50, risk_score=0.9)
        assert conf_high_risk < conf_low_risk

    def test_multi_signal_boost(self):
        conf, signals = self.scorer.compute(probability=50, risk_score=0.5, signal_count=8)
        assert "MULTI_SIGNAL_CONFIRMATION" in signals

    def test_low_signal_warning(self):
        conf, signals = self.scorer.compute(probability=50, risk_score=0.5, signal_count=0)
        assert "LOW_SIGNAL_WARNING" in signals

    def test_high_intelligence_boost(self):
        conf, signals = self.scorer.compute(probability=50, risk_score=0.5,
                                            intelligence_confidence=0.85, signal_count=3)
        assert "HIGH_INTELLIGENCE_BOOST" in signals

    def test_confidence_bounds(self):
        conf, _ = self.scorer.compute(probability=200, risk_score=0.0, signal_count=20)
        assert conf <= 100
        conf2, _ = self.scorer.compute(probability=-10, risk_score=0.5)
        assert conf2 >= 0


class TestMarketFilter:

    def setup_method(self):
        self.filter = MarketFilter()

    def test_btc_bearish_contradicts_bullish(self):
        r = ScanResult(symbol="BTC", trend_score=0.0, momentum_score=0.0,
                       breakout_score=0.0, reversal_score=0.0, liquidity_score=0.0,
                       features={"trend": "BULLISH"})
        should, reason = self.filter.should_filter(r, side="LONG", btc_trend="BEARISH")
        assert should
        assert "BTC_BEARISH_CONTRADICTS" in reason

    def test_extreme_greed_with_reversal(self):
        r = ScanResult(symbol="BTC", trend_score=0.0, momentum_score=0.6,
                       breakout_score=0.0, reversal_score=0.4, liquidity_score=0.0,
                       features={"trend": "BULLISH"})
        should, reason = self.filter.should_filter(r, side="LONG", fear_greed_label="EXTREME_GREED")
        assert should

    def test_market_closed(self):
        r = ScanResult(symbol="BTC")
        should, reason = self.filter.should_filter(r, market_session="CLOSED")
        assert should
        assert "MARKET_CLOSED" in reason

    def test_normal_market_no_filter(self):
        r = ScanResult(symbol="BTC")
        should, reason = self.filter.should_filter(r, side="LONG", btc_trend="BULLISH")
        assert not should
        assert reason is None

    def test_bullish_trend_but_ranked_short_with_bearish_btc_kept(self):
        # features["trend"] is BULLISH but the real ranked side is SHORT, and BTC
        # is BEARISH — a bearish BTC context confirms a SHORT, it doesn't contradict it.
        r = ScanResult(symbol="BTC", trend_score=0.6, momentum_score=-0.9,
                       breakout_score=-0.8, reversal_score=-0.7, liquidity_score=0.0,
                       features={"trend": "BULLISH"})
        should, reason = self.filter.should_filter(r, side="SHORT", btc_trend="BEARISH")
        assert not should
        assert reason is None

    def test_genuine_contradiction_long_with_bearish_btc_filtered(self):
        r = ScanResult(symbol="BTC", trend_score=0.6, momentum_score=0.5,
                       breakout_score=0.5, reversal_score=0.5, liquidity_score=0.0,
                       features={"trend": "BULLISH"})
        should, reason = self.filter.should_filter(r, side="LONG", btc_trend="BEARISH")
        assert should
        assert "BTC_BEARISH_CONTRADICTS" in reason


class TestScannerMarketFilterIntegration:
    def test_scanner_keeps_short_opportunity_with_bearish_btc(self):
        # Prove that an opportunity with features["trend"]=BULLISH but a real
        # ranked side of SHORT is kept when btc_trend=BEARISH (a confirming
        # signal for a SHORT, not a contradiction).
        from market.models import Asset, AssetMetadata
        from scanner.core import OpportunityScanner
        from scanner.models import Opportunity

        mock_service = MagicMock()
        mock_ranker = MagicMock()
        mock_ranker.rank.return_value = [
            Opportunity(symbol="BTCUSDT", side="SHORT", strategy="reversal", score=0.5, confidence=50.0)
        ]

        ohlcv = pd.DataFrame({"close": [50000.0], "volume": [100.0]})
        asset = Asset(
            symbol="BTCUSDT",
            metadata=AssetMetadata(symbol="BTCUSDT"),
            price=50000.0,
            ohlcv=ohlcv,
            indicators={"ema20": 110, "ema50": 105, "ema200": 100, "rsi": 60},
            features={"trend": "BULLISH", "momentum": "STRONG", "liquidity": "HIGH", "risk": "LOW", "volatility_class": "NORMAL"},
        )
        asset.context = {"session": "OPEN", "btc": {"btc_trend": "BEARISH"}}
        mock_service.get_asset.return_value = asset

        scanner = OpportunityScanner(market_service=mock_service, ranker=mock_ranker, symbols=["BTCUSDT"])
        ops = scanner.scan()
        assert len(ops) == 1
        assert ops[0].symbol == "BTCUSDT"
        assert ops[0].side == "SHORT"


class TestFalseSignalFilter:

    def setup_method(self):
        self.filter = FalseSignalFilter()

    def test_low_volume_breakout(self):
        r = ScanResult(symbol="BTC", breakout_score=0.5, signals=[])
        should, reason = self.filter.should_filter(r, volume_score=0.2)
        assert should
        assert "LOW_VOLUME_BREAKOUT" in reason

    def test_high_volume_breakout_not_filtered(self):
        r = ScanResult(symbol="BTC", breakout_score=0.5, signals=[])
        should, reason = self.filter.should_filter(r, volume_score=0.8)
        assert not should

    def test_trend_reversal_conflict(self):
        r = ScanResult(symbol="BTC", trend_score=0.5, reversal_score=0.5, signals=[])
        should, reason = self.filter.should_filter(r)
        assert should
        assert "TREND_REVERSAL_CONFLICT" in reason

    def test_rsi_overbought_with_bullish(self):
        r = ScanResult(symbol="BTC", signals=["RSI_OVERBOUGHT", "RSI_BULLISH"])
        should, reason = self.filter.should_filter(r)
        assert should

    def test_no_filter(self):
        r = ScanResult(symbol="BTC", signals=[])
        should, reason = self.filter.should_filter(r)
        assert not should


class TestWatchlistEngine:

    def setup_method(self):
        self.engine = WatchlistEngine()

    def test_create_and_get(self):
        result = self.engine.create("alts", ["ETHUSDT", "SOLUSDT"])
        assert result["count"] == 2
        wl = self.engine.get("alts")
        assert wl["name"] == "alts"
        assert "SOLUSDT" in wl["symbols"]

    def test_create_duplicate(self):
        self.engine.create("wl", ["BTC"])
        result = self.engine.create("wl", ["ETH"])
        assert "error" in result

    def test_add_symbol(self):
        self.engine.create("wl", ["BTC"])
        result = self.engine.add_symbol("ETH", "wl")
        assert result["count"] == 2

    def test_remove_symbol(self):
        self.engine.create("wl", ["BTC", "ETH"])
        result = self.engine.remove_symbol("BTC", "wl")
        assert result["count"] == 1

    def test_list_all(self):
        self.engine.create("a", ["BTC"])
        self.engine.create("b", ["ETH"])
        wls = self.engine.list_all()
        assert len(wls) == 2

    def test_filter_opportunities(self):
        self.engine.create("my_wl", ["BTCUSDT"])
        ops = [
            Opportunity(symbol="BTCUSDT", side="LONG", strategy="trend", score=0.8, confidence=80.0),
            Opportunity(symbol="ETHUSDT", side="LONG", strategy="trend", score=0.5, confidence=50.0),
        ]
        filtered = self.engine.filter_opportunities(ops, "my_wl")
        assert len(filtered) == 1
        assert filtered[0].symbol == "BTCUSDT"

    def test_filter_no_symbols_returns_all(self):
        ops = [Opportunity(symbol="BTCUSDT", side="LONG", strategy="trend", score=0.8, confidence=80.0)]
        filtered = self.engine.filter_opportunities(ops)
        assert len(filtered) == 1

    def test_set_active(self):
        self.engine.create("a", ["BTC"])
        self.engine.create("b", ["ETH"])
        self.engine.set_active("b")
        assert self.engine.active_symbols == ["ETH"]


class TestDTO:

    def test_opportunity_to_dto(self):
        opp = Opportunity(
            symbol="BTCUSDT", side="LONG", strategy="trend",
            score=0.8, confidence=80.0, price=50000, rank=1,
            signals=["BULLISH_TREND"],
            probability_score=75.0, risk_score=0.3,
        )
        dto = opportunity_to_dto(opp)
        assert dto["rank"] == 1
        assert dto["symbol"] == "BTCUSDT"
        assert dto["probability"] == 75.0
        assert dto["risk_score"] == 0.3

    def test_dashboard_dto(self):
        dto = ScannerDashboardDTO(
            symbols_scanned=10,
            opportunities_found=3,
            top_opportunities=[],
            top_signals=[],
            market_summary={},
            intelligence_summary={},
            timestamp="2025-01-01T00:00:00",
        )
        assert dto.symbols_scanned == 10
        assert dto.opportunities_found == 3
