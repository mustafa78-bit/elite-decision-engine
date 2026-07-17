from datetime import datetime, timezone

from whale.models import TransferEvent
from whale.integration import WhaleIntegration
from liquidity.integration import LiquidityIntegration
from orderflow.integration import OrderFlowIntegration
from orderflow.models import Trade
from market_structure.integration import MarketStructureIntegration
from market_structure.models import PriceCandle
from news.integration import NewsIntegration
from news.models import NewsEvent
from sentiment.integration import SentimentIntegration
from sentiment.models import SentimentEvent
from macro.integration import MacroIntegration
from core.intelligence import IntelligenceBundle
from scoring.engine import ScoringEngine


class TestWhaleIntegration:

    def make_transfer(
        self, from_addr="0xa", to_addr="0xb", value=100000.0, seq=0
    ):
        return TransferEvent(
            tx_id=f"tx_{from_addr[:4]}_{to_addr[:4]}_{seq}",
            from_address=from_addr,
            to_address=to_addr,
            asset="BTC",
            amount=value / 50000,
            value_usd=value,
            timestamp=datetime.now(timezone.utc),
        )

    def test_process_transfer_disabled(self):
        integration = WhaleIntegration()
        integration.enabled = False
        transfer = self.make_transfer()
        event = integration.process_transfer(transfer)
        assert event is None

    def test_process_transfer_enabled(self):
        integration = WhaleIntegration()
        transfer = self.make_transfer(value=500000.0)
        event = integration.process_transfer(transfer)
        assert event is not None
        assert event.event_type == "LARGE_TRANSFER"

    def test_process_transfer_small(self):
        integration = WhaleIntegration()
        transfer = self.make_transfer(value=100.0)
        event = integration.process_transfer(transfer)
        assert event is not None
        assert event.event_type == "TRANSFER"

    def test_get_whale_signals(self):
        integration = WhaleIntegration()
        for i in range(12):
            t = self.make_transfer(f"0xwhale{i}", "0xdest", 300000.0)
            integration.process_transfer(t)
        signals = integration.get_whale_signals()
        assert isinstance(signals, list)

    def test_get_whale_signals_disabled(self):
        integration = WhaleIntegration()
        integration.enabled = False
        assert integration.get_whale_signals() == []

    def test_get_features_enabled(self):
        integration = WhaleIntegration()
        features = integration.get_features()
        assert features["whale_enabled"] is True
        assert "whale_features" in features

    def test_get_features_disabled(self):
        integration = WhaleIntegration()
        integration.enabled = False
        features = integration.get_features()
        assert features["whale_enabled"] is False

    def test_get_features_tracks_counts(self):
        integration = WhaleIntegration()
        integration.process_transfer(self.make_transfer(value=500000.0))
        features = integration.get_features()
        wf = features["whale_features"]
        assert wf["recent_large_transfer_count"] >= 1
        assert wf["total_large_transfer_volume"] >= 500000.0

    def test_get_contribution_log_empty(self):
        integration = WhaleIntegration()
        log = integration.get_contribution_log()
        assert log == []

    def test_get_contribution_log_with_events(self):
        integration = WhaleIntegration()
        integration.process_transfer(self.make_transfer(value=500000.0))
        log = integration.get_contribution_log()
        assert len(log) == 1
        assert log[0]["value_usd"] == 500000.0

    def test_evaluate_enabled(self):
        integration = WhaleIntegration()
        result = integration.evaluate()
        assert result["ok"] is True
        assert result["whale_available"] is True

    def test_evaluate_disabled(self):
        integration = WhaleIntegration()
        integration.enabled = False
        result = integration.evaluate()
        assert result["ok"] is True
        assert result["whale_available"] is False

    def test_multiple_transfers(self):
        integration = WhaleIntegration()
        for i in range(5):
            integration.process_transfer(
                self.make_transfer(value=100000.0 * (i + 1), seq=i)
            )
        assert len(integration.events) == 5


def _build_intelligence_data(
    whale_features=None,
    liquidity_features=None,
    orderflow_features=None,
    ms_features=None,
    news_features=None,
    sentiment_features=None,
    macro_features=None,
):
    data = {
        "btc": {"ok": True, "score": 1.0},
        "whale": {"whale_available": False},
        "liquidity": {"liquidity_available": False},
        "orderflow": {"orderflow_available": False},
        "market_structure": {"market_structure_available": False},
        "news": {"news_available": False},
        "sentiment": {"sentiment_available": False},
        "macro": {"macro_available": False},
    }
    if whale_features:
        data["whale"] = {
            "ok": True,
            "whale_available": True,
            "features": {"whale_features": whale_features},
        }
    if liquidity_features:
        data["liquidity"] = {
            "ok": True,
            "liquidity_available": True,
            "features": {"liquidity_features": liquidity_features},
        }
    if orderflow_features:
        data["orderflow"] = {
            "ok": True,
            "orderflow_available": True,
            "features": {"orderflow_features": orderflow_features},
        }
    if ms_features:
        data["market_structure"] = {
            "ok": True,
            "market_structure_available": True,
            "features": {"market_structure_features": ms_features},
        }
    if news_features:
        data["news"] = {
            "ok": True,
            "news_available": True,
            "features": {"news_features": news_features},
        }
    if sentiment_features:
        data["sentiment"] = {
            "ok": True,
            "sentiment_available": True,
            "features": {"sentiment_features": sentiment_features},
        }
    if macro_features:
        data["macro"] = {
            "ok": True,
            "macro_available": True,
            "features": {"macro_features": macro_features},
        }
    return data


class TestIntelligenceBundle:

    def test_default_no_modules(self):
        bundle = IntelligenceBundle()
        result = bundle.evaluate()
        assert result["btc"]["ok"] is True
        assert result["whale"]["whale_available"] is False
        assert result["liquidity"]["liquidity_available"] is False
        assert result["orderflow"]["orderflow_available"] is False
        assert result["market_structure"]["market_structure_available"] is False
        assert result["news"]["news_available"] is False
        assert result["sentiment"]["sentiment_available"] is False
        assert result["macro"]["macro_available"] is False

    def test_with_whale_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_whale(WhaleIntegration())
        result = bundle.evaluate()
        assert result["whale"]["whale_available"] is True

    def test_with_liquidity_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_liquidity(LiquidityIntegration())
        result = bundle.evaluate()
        assert result["liquidity"]["liquidity_available"] is True

    def test_with_orderflow_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_orderflow(OrderFlowIntegration())
        result = bundle.evaluate()
        assert result["orderflow"]["orderflow_available"] is True

    def test_with_market_structure_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_market_structure(MarketStructureIntegration())
        result = bundle.evaluate()
        assert result["market_structure"]["market_structure_available"] is True

    def test_with_news_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_news(NewsIntegration())
        result = bundle.evaluate()
        assert result["news"]["news_available"] is True

    def test_with_sentiment_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_sentiment(SentimentIntegration())
        result = bundle.evaluate()
        assert result["sentiment"]["sentiment_available"] is True

    def test_with_macro_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_macro(MacroIntegration())
        result = bundle.evaluate()
        assert result["macro"]["macro_available"] is True

    def test_all_modules_enabled(self):
        bundle = IntelligenceBundle()
        bundle.enable_whale(WhaleIntegration())
        bundle.enable_liquidity(LiquidityIntegration())
        bundle.enable_orderflow(OrderFlowIntegration())
        bundle.enable_market_structure(MarketStructureIntegration())
        bundle.enable_news(NewsIntegration())
        bundle.enable_sentiment(SentimentIntegration())
        bundle.enable_macro(MacroIntegration())
        result = bundle.evaluate()
        for key in ("whale", "liquidity", "orderflow", "market_structure", "news", "sentiment", "macro"):
            assert result[key][f"{key}_available"] is True

    def test_get_all_features_without_modules(self):
        bundle = IntelligenceBundle()
        features = bundle.get_all_features()
        assert "btc_health" in features
        for key in ("whale", "liquidity", "orderflow", "market_structure", "news", "sentiment", "macro"):
            assert key not in features

    def test_get_all_features_with_all_modules(self):
        bundle = IntelligenceBundle()
        bundle.enable_whale(WhaleIntegration())
        bundle.enable_liquidity(LiquidityIntegration())
        bundle.enable_orderflow(OrderFlowIntegration())
        bundle.enable_market_structure(MarketStructureIntegration())
        bundle.enable_news(NewsIntegration())
        bundle.enable_sentiment(SentimentIntegration())
        bundle.enable_macro(MacroIntegration())
        features = bundle.get_all_features()
        for key in ("whale", "liquidity", "orderflow", "market_structure", "news", "sentiment", "macro"):
            assert key in features

    def test_evaluate_always_returns_btc(self):
        bundle = IntelligenceBundle()
        result = bundle.evaluate()
        assert result["btc"]["ok"] is True

    def test_monitoring_tracks_calls(self):
        bundle = IntelligenceBundle()
        bundle.evaluate()
        bundle.evaluate()
        assert bundle.monitoring["evaluate_calls"] == 2


class TestIntelligenceBundleBackwardCompatibility:

    def test_whale_only_still_works(self):
        bundle = IntelligenceBundle()
        bundle.enable_whale(WhaleIntegration())
        result = bundle.evaluate()
        assert "whale" in result
        assert "liquidity" in result
        assert "orderflow" in result
        assert "market_structure" in result
        assert "news" in result
        assert "sentiment" in result
        assert "macro" in result

    def test_disabled_whale_safe(self):
        bundle = IntelligenceBundle()
        whale = WhaleIntegration()
        whale.enabled = False
        bundle.enable_whale(whale)
        result = bundle.evaluate()
        assert result["whale"]["whale_available"] is False

    def test_empty_evaluate_safe(self):
        bundle = IntelligenceBundle()
        result = bundle.evaluate({})
        assert result["btc"]["ok"] is True


class TestScoringEngine:

    def test_score_signal_no_data(self):
        engine = ScoringEngine()
        result = engine.score_signal({"base_score": 50})
        assert result["score"] == 50
        assert result["whale_used"] is False
        assert result["liquidity_used"] is False
        assert result["orderflow_used"] is False
        assert result["market_structure_used"] is False

    def test_score_signal_with_whale(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            whale_features={"whale_enabled": True, "recent_large_transfer_count": 5}
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["whale_used"] is True

    def test_score_signal_whale_disabled(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            whale_features={"whale_enabled": False, "recent_large_transfer_count": 5}
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] == 50

    def test_score_signal_capped_at_100(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            whale_features={"whale_enabled": True, "recent_large_transfer_count": 100}
        )
        result = engine.score_signal({"base_score": 90}, data)
        assert result["score"] <= 100

    def test_score_signal_with_liquidity(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            liquidity_features={"active_zone_count": 5}
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["liquidity_used"] is True

    def test_score_signal_with_orderflow_rising(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            orderflow_features={
                "orderflow_enabled": True, "cvd_trend": "RISING"
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["orderflow_used"] is True

    def test_score_signal_with_orderflow_falling(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            orderflow_features={
                "orderflow_enabled": True, "cvd_trend": "FALLING"
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] < 50
        assert result["orderflow_used"] is True

    def test_score_signal_with_ms_bullish(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            ms_features={
                "market_structure_enabled": True, "trend": "BULLISH"
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["market_structure_used"] is True

    def test_score_signal_with_ms_bearish(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            ms_features={
                "market_structure_enabled": True, "trend": "BEARISH"
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] < 50
        assert result["market_structure_used"] is True

    def test_score_signal_all_sources(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            whale_features={"whale_enabled": True, "recent_large_transfer_count": 3},
            liquidity_features={"active_zone_count": 4},
            orderflow_features={"orderflow_enabled": True, "cvd_trend": "RISING"},
            ms_features={"market_structure_enabled": True, "trend": "BULLISH"},
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["whale_used"] is True
        assert result["liquidity_used"] is True
        assert result["orderflow_used"] is True
        assert result["market_structure_used"] is True

    def test_score_signal_boosts_tracking(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            whale_features={"whale_enabled": True, "recent_large_transfer_count": 5},
            orderflow_features={"orderflow_enabled": True, "cvd_trend": "RISING"},
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["boosts"]["whale"] is True
        assert result["boosts"]["orderflow"] is True
        assert result["boosts"]["liquidity"] is False

    def test_score_signal_with_intelligence(self):
        bundle = IntelligenceBundle()
        bundle.enable_whale(WhaleIntegration())
        engine = ScoringEngine(intelligence=bundle)
        result = engine.score_signal({"base_score": 50})
        assert result["score"] == 50
        assert result["whale_used"] is False

    def test_score_signal_missing_sources_safe(self):
        engine = ScoringEngine()
        data = {
            "btc": {"ok": True},
            "whale": {"whale_available": False},
        }
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] == 50

    def test_score_signal_no_negative_below_zero(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            orderflow_features={"orderflow_enabled": True, "cvd_trend": "FALLING"},
            ms_features={"market_structure_enabled": True, "trend": "BEARISH"},
        )
        result = engine.score_signal({"base_score": 5}, data)
        assert result["score"] >= 0

    def test_score_signal_with_news_bullish(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            news_features={"news_enabled": True, "dominant_sentiment": "BULLISH"}
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["news_used"] is True
        assert result["boosts"]["news"] is True

    def test_score_signal_with_news_bearish(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            news_features={"news_enabled": True, "dominant_sentiment": "BEARISH"}
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] < 50

    def test_score_signal_with_sentiment_bullish(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            sentiment_features={
                "sentiment_enabled": True, "bullish_assets": 3, "bearish_assets": 0
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["sentiment_used"] is True

    def test_score_signal_with_sentiment_bearish(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            sentiment_features={
                "sentiment_enabled": True, "bullish_assets": 0, "bearish_assets": 4
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] < 50

    def test_score_signal_with_macro_greed(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            macro_features={
                "macro_enabled": True,
                "fear_greed": {"classification": "GREED", "value": 70},
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["macro_used"] is True

    def test_score_signal_with_macro_fear(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            macro_features={
                "macro_enabled": True,
                "fear_greed": {"classification": "EXTREME_FEAR", "value": 15},
            }
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] < 50

    def test_score_signal_all_sources_extended(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            whale_features={"whale_enabled": True, "recent_large_transfer_count": 3},
            liquidity_features={"active_zone_count": 4},
            orderflow_features={"orderflow_enabled": True, "cvd_trend": "RISING"},
            ms_features={"market_structure_enabled": True, "trend": "BULLISH"},
            news_features={"news_enabled": True, "dominant_sentiment": "BULLISH"},
            sentiment_features={
                "sentiment_enabled": True, "bullish_assets": 2, "bearish_assets": 0
            },
            macro_features={
                "macro_enabled": True,
                "fear_greed": {"classification": "GREED", "value": 70},
            },
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["score"] > 50
        assert result["whale_used"] is True
        assert result["liquidity_used"] is True
        assert result["orderflow_used"] is True
        assert result["market_structure_used"] is True
        assert result["news_used"] is True
        assert result["sentiment_used"] is True
        assert result["macro_used"] is True

    def test_score_signal_boosts_tracking_extended(self):
        engine = ScoringEngine()
        data = _build_intelligence_data(
            whale_features={"whale_enabled": True, "recent_large_transfer_count": 5},
            news_features={"news_enabled": True, "dominant_sentiment": "BULLISH"},
        )
        result = engine.score_signal({"base_score": 50}, data)
        assert result["boosts"]["whale"] is True
        assert result["boosts"]["news"] is True
        assert result["boosts"]["sentiment"] is False
        assert result["boosts"]["macro"] is False
