from unittest.mock import MagicMock, patch

from decision.models import DecisionContext, DecisionExplanation, DecisionSnapshot
from decision.confidence import AdaptiveConfidenceEngine, ConfidenceBreakdown, CONFIDENCE_THRESHOLDS
from scoring.engine import ScoringEngine
from core.intelligence import IntelligenceBundle


class MockSignal:
    def __init__(self, symbol="BTC", side="LONG", timeframe="1h", score=50.0, id=1):
        self.symbol = symbol
        self.side = side
        self.timeframe = timeframe
        self.score = score
        self.id = id


class TestDecisionEngineHistory:

    def test_decision_history_added(self):
        from core.engine import DecisionEngine
        engine = DecisionEngine()
        mock_signal = MockSignal()
        with patch.object(engine.intelligence, "evaluate", return_value={
            "btc": {"ok": True, "score": 1.0},
            "whale": {"ok": True, "whale_available": True, "features": {"whale_features": {"whale_enabled": True}}},
            "liquidity": {"ok": True, "liquidity_available": True},
            "orderflow": {"ok": True, "orderflow_available": True},
            "market_structure": {"ok": True, "market_structure_available": True},
            "news": {"ok": True, "news_available": True},
            "sentiment": {"ok": True, "sentiment_available": True},
            "macro": {"ok": True, "macro_available": True},
        }):
            engine.process_signal(mock_signal)
        assert len(engine.decision_history) == 1
        snap = engine.decision_history[0]
        assert snap.decision == "APPROVED"
        assert snap.signal_id == 1

    def test_decision_history_btc_rejection(self):
        from core.engine import DecisionEngine
        engine = DecisionEngine()
        mock_signal = MockSignal(side="LONG")
        with patch.object(engine.intelligence, "evaluate", return_value={
            "btc": {"ok": False, "score": 0.0},
            "whale": {"ok": True, "whale_available": True},
            "liquidity": {"ok": True, "liquidity_available": True},
            "orderflow": {"ok": True, "orderflow_available": True},
            "market_structure": {"ok": True, "market_structure_available": True},
            "news": {"ok": True, "news_available": True},
            "sentiment": {"ok": True, "sentiment_available": True},
            "macro": {"ok": True, "macro_available": True},
        }):
            engine.process_signal(mock_signal)
        assert len(engine.decision_history) == 1
        snap = engine.decision_history[0]
        assert snap.decision == "REJECTED"

    def test_get_decision_history(self):
        from core.engine import DecisionEngine
        engine = DecisionEngine()
        mock_signal = MockSignal()
        with patch.object(engine.intelligence, "evaluate", return_value={
            "btc": {"ok": True, "score": 1.0},
            "whale": {"ok": True, "whale_available": True},
            "liquidity": {"ok": True, "liquidity_available": True},
            "orderflow": {"ok": True, "orderflow_available": True},
            "market_structure": {"ok": True, "market_structure_available": True},
            "news": {"ok": True, "news_available": True},
            "sentiment": {"ok": True, "sentiment_available": True},
            "macro": {"ok": True, "macro_available": True},
        }):
            engine.process_signal(mock_signal)
        history = engine.get_decision_history()
        assert len(history) == 1
        assert history[0]["decision"] == "APPROVED"

    def test_decision_history_max_size(self):
        from core.engine import DecisionEngine
        engine = DecisionEngine()
        engine._max_history = 2
        for i in range(5):
            mock_signal = MockSignal(id=i)
            with patch.object(engine.intelligence, "evaluate", return_value={
                "btc": {"ok": True, "score": 1.0},
                "whale": {"ok": True, "whale_available": True},
                "liquidity": {"ok": True, "liquidity_available": True},
                "orderflow": {"ok": True, "orderflow_available": True},
                "market_structure": {"ok": True, "market_structure_available": True},
                "news": {"ok": True, "news_available": True},
                "sentiment": {"ok": True, "sentiment_available": True},
                "macro": {"ok": True, "macro_available": True},
            }):
                engine.process_signal(mock_signal)
        assert len(engine.decision_history) == 2


class TestScoringEngineConfidence:

    def test_confidence_breakdown_in_result(self):
        engine = ScoringEngine()
        result = engine.score_signal({"base_score": 50})
        assert "confidence_breakdown" in result
        assert result["confidence_breakdown"]["base_confidence"] == 50.0
        assert "final_confidence" in result["confidence_breakdown"]

    def test_confidence_label_in_result(self):
        engine = ScoringEngine()
        result = engine.score_signal({"base_score": 50})
        assert "confidence_label" in result
        assert result["confidence_label"] == "NEUTRAL"

    def test_boost_values_in_result(self):
        engine = ScoringEngine()
        result = engine.score_signal({"base_score": 50})
        assert "boost_values" in result
        assert result["boost_values"]["whale"] == 0


class TestBackwardCompatibility:

    def test_decision_engine_still_prints(self):
        from core.engine import DecisionEngine
        engine = DecisionEngine()
        assert engine.intelligence is not None

    def test_scoring_engine_no_intelligence_no_crash(self):
        engine = ScoringEngine()
        result = engine.score_signal({"base_score": 50})
        assert result["score"] == 50

    def test_intelligence_bundle_has_fusion(self):
        bundle = IntelligenceBundle()
        result = bundle.evaluate()
        assert "_fusion" in result
        assert "unified_score" in result["_fusion"]
