from __future__ import annotations

import pytest
from datetime import datetime, timezone

from dto.explanations import (
    ConfidenceBreakdownDTO,
    DecisionExplanationDTO,
    DecisionMetadataDTO,
    DecisionReasoningDTO,
    DecisionTimelineDTO,
    IntelligenceContributionDTO,
    MarketContributionDTO,
    MemoryContributionDTO,
    RiskContributionDTO,
    StrategyContributionDTO,
)
from services.explanation_service import ExplanationService


class FakeSignal:
    def __init__(self, sid=1, symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN"):
        self.id = sid
        self.symbol = symbol
        self.side = side
        self.timeframe = timeframe
        self.status = status


class TestExplanationDTOs:

    def test_confidence_breakdown_to_dict(self):
        dto = ConfidenceBreakdownDTO(
            trend_score=0.8, volume_score=0.6, btc_score=0.7, mtf_score=0.5, risk_score=0.9,
            trend_contribution=0.24, volume_contribution=0.12, btc_contribution=0.14,
            mtf_contribution=0.10, risk_contribution=0.09,
            final_score=0.69, confidence=69.0, decision="WATCH",
        )
        d = dto.to_dict()
        assert d["trend_score"] == 0.8
        assert d["final_score"] == 0.69
        assert d["decision"] == "WATCH"

    def test_risk_contribution_to_dict(self):
        dto = RiskContributionDTO(atr=1500, volatility_score=0.05, risk_score=0.8, penalties={"volatility": 0.03}, atr_impact="high")
        d = dto.to_dict()
        assert d["atr"] == 1500
        assert d["atr_impact"] == "high"

    def test_intelligence_contribution_to_dict(self):
        dto = IntelligenceContributionDTO(confidence=0.75, feature_count=2, available_features=["funding", "open_interest"])
        d = dto.to_dict()
        assert d["confidence"] == 0.75
        assert d["feature_count"] == 2

    def test_market_contribution_to_dict(self):
        dto = MarketContributionDTO(symbol="BTCUSDT", price=50000, rsi=55, regime="TREND")
        d = dto.to_dict()
        assert d["symbol"] == "BTCUSDT"
        assert d["regime"] == "TREND"

    def test_strategy_contribution_to_dict(self):
        dto = StrategyContributionDTO(strategy_name="TestStrategy", confidence=0.8, score=0.75)
        d = dto.to_dict()
        assert d["strategy_name"] == "TestStrategy"

    def test_memory_contribution_to_dict(self):
        dto = MemoryContributionDTO(total_entries=10, wins=7, losses=3, win_rate_pct=70.0, total_pnl=1500.0)
        d = dto.to_dict()
        assert d["total_entries"] == 10
        assert d["win_rate_pct"] == 70.0

    def test_decision_reasoning_to_dict(self):
        dto = DecisionReasoningDTO(
            signal_id=1, symbol="BTCUSDT", side="LONG", timeframe="1h",
            entry_price=50000, status="OPEN", decision="APPROVE",
            confidence_breakdown=ConfidenceBreakdownDTO(confidence=85.0, decision="APPROVE"),
            human_readable="Decision: APPROVE | Signal: BTCUSDT LONG (1h)",
        )
        d = dto.to_dict()
        assert d["signal_id"] == 1
        assert d["decision"] == "APPROVE"
        assert d["confidence_breakdown"]["confidence"] == 85.0

    def test_decision_timeline_add_event(self):
        dto = DecisionTimelineDTO(signal_id=1)
        assert len(dto.events) == 0
        dto.add_event("test_event", "test detail")
        assert len(dto.events) == 1
        assert dto.events[0]["event"] == "test_event"
        assert dto.events[0]["detail"] == "test detail"

    def test_decision_metadata_to_dict(self):
        dto = DecisionMetadataDTO(signal_id=1, processing_time_ms=150.5)
        d = dto.to_dict()
        assert d["signal_id"] == 1
        assert d["processing_time_ms"] == 150.5

    def test_decision_explanation_to_dict(self):
        reasoning = DecisionReasoningDTO(signal_id=1)
        timeline = DecisionTimelineDTO(signal_id=1)
        metadata = DecisionMetadataDTO(signal_id=1)
        dto = DecisionExplanationDTO(reasoning=reasoning, timeline=timeline, metadata=metadata)
        d = dto.to_dict()
        assert "reasoning" in d
        assert "timeline" in d
        assert "metadata" in d


class TestExplanationService:

    def test_explain_signal_without_scores(self):
        service = ExplanationService()
        signal = FakeSignal()
        explanation = service.explain_signal(signal)
        assert explanation.reasoning is not None
        assert explanation.timeline is not None
        assert explanation.metadata is not None
        assert explanation.reasoning.signal_id == 1
        assert explanation.reasoning.symbol == "BTCUSDT"
        assert explanation.timeline.signal_id == 1
        assert len(explanation.timeline.events) == 2

    def test_explain_signal_with_scores(self):
        service = ExplanationService()
        signal = FakeSignal()
        scores = {
            "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0,
            "ema200": 50200.0, "rsi": 55.0, "atr": 500.0,
            "trend_score": 1.0, "volume_score": 0.8, "btc_score": 0.7,
            "mtf_score": 0.6, "risk_score": 0.5, "final_score": 0.78,
            "confidence": 78.0,
            "volatility_score": 0.03,
            "contributions": {
                "trend": 0.30, "volume": 0.16, "btc": 0.14,
                "mtf": 0.12, "risk": 0.05,
            },
        }
        explanation = service.explain_signal(signal, scores)
        assert explanation.reasoning is not None
        assert explanation.reasoning.decision == "WATCH"
        assert explanation.reasoning.confidence_breakdown is not None
        assert explanation.reasoning.confidence_breakdown.final_score == 0.78
        assert explanation.reasoning.market_contribution is not None
        assert explanation.reasoning.market_contribution.symbol == "BTCUSDT"
        assert explanation.reasoning.risk_contribution is not None
        assert explanation.reasoning.risk_contribution.atr == 500
        assert explanation.reasoning.human_readable != ""

    def test_human_readable_contains_decision(self):
        service = ExplanationService()
        signal = FakeSignal()
        scores = {
            "entry": 50000.0, "trend_score": 1.0, "volume_score": 0.8,
            "btc_score": 0.7, "mtf_score": 0.6, "risk_score": 0.5,
            "final_score": 0.85, "confidence": 90.0, "atr": 500,
            "rsi": 55, "ema20": 51000, "ema50": 50500, "ema200": 50200,
            "volatility_score": 0.03,
            "contributions": {"trend": 0.30, "volume": 0.16, "btc": 0.14, "mtf": 0.12, "risk": 0.05},
        }
        explanation = service.explain_signal(signal, scores)
        assert "Decision: STRONG_APPROVE" in explanation.reasoning.human_readable
        assert "BTCUSDT" in explanation.reasoning.human_readable
        assert "LONG" in explanation.reasoning.human_readable

    def test_explain_signal_multiple_signals(self):
        service = ExplanationService()
        signals = [
            FakeSignal(sid=1, symbol="BTCUSDT", side="LONG"),
            FakeSignal(sid=2, symbol="ETHUSDT", side="SHORT"),
        ]
        for s in signals:
            explanation = service.explain_signal(s)
            assert explanation.reasoning.symbol == s.symbol
            assert explanation.reasoning.side == s.side

    def test_explain_signal_none_fields(self):
        service = ExplanationService()

        class PartialSignal:
            id = 0
            symbol = ""
            side = ""
            timeframe = ""
            status = ""

        signal = PartialSignal()
        explanation = service.explain_signal(signal)
        assert explanation.reasoning is not None
        assert explanation.metadata is not None

    def test_confidence_breakdown_decision_thresholds(self):
        service = ExplanationService()

        test_cases = [
            (95.0, "STRONG_APPROVE"),
            (85.0, "APPROVE"),
            (75.0, "WATCH"),
            (50.0, "REJECT"),
        ]
        for confidence, expected_decision in test_cases:
            signal = FakeSignal()
            scores = {
                "trend_score": 1.0, "volume_score": 1.0, "btc_score": 1.0,
                "mtf_score": 1.0, "risk_score": 1.0, "final_score": 0.5,
                "confidence": confidence,
                "volatility_score": 0.0, "atr": 500, "rsi": 50,
                "entry": 50000, "ema20": 50000, "ema50": 50000, "ema200": 50000,
                "contributions": {"trend": 0, "volume": 0, "btc": 0, "mtf": 0, "risk": 0},
            }
            explanation = service.explain_signal(signal, scores)
            assert explanation.reasoning.decision == expected_decision, f"Expected {expected_decision} for confidence={confidence}, got {explanation.reasoning.decision}"

    def test_risk_contribution_atr_impact(self):
        service = ExplanationService()
        scores_low = {"atr": 500, "volatility_score": 0.01, "risk_score": 1.0}
        scores_high = {"atr": 2000, "volatility_score": 0.05, "risk_score": 0.5}

        rc_low = service._build_risk_contribution(scores_low)
        rc_high = service._build_risk_contribution(scores_high)

        assert rc_low.atr_impact == "moderate"
        assert rc_high.atr_impact == "high"

    def test_build_metadata(self):
        service = ExplanationService()
        signal = FakeSignal()
        metadata = service._build_metadata(signal, 150.5)
        assert metadata.signal_id == 1
        assert metadata.processing_time_ms == 150.5
        assert metadata.total_sources_evaluated == 6
        assert metadata.explanation_version == "2.0"
