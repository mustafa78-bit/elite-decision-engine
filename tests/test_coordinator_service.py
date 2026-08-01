from __future__ import annotations

import pytest

from dto.coordination import (
    ConfidenceAggregationDTO,
    ConflictResolutionDTO,
    ConsensusScoreDTO,
    CoordinatorDiagnosticsDTO,
    CoordinatorReportDTO,
    IntelligenceSourceDTO,
    RecommendationRankingDTO,
    SourcePriorityDTO,
)
from services.coordinator_service import (
    AISourceRegistry,
    CoordinatorService,
    IntelligenceRegistry,
)


class FakeSignal:
    def __init__(self, sid=1, symbol="BTCUSDT", side="LONG", timeframe="1h"):
        self.id = sid
        self.symbol = symbol
        self.side = side
        self.timeframe = timeframe


class TestCoordinationDTOs:

    def test_intelligence_source_to_dict(self):
        dto = IntelligenceSourceDTO(name="ScoringEngine", source_type="scoring", confidence=0.8, available=True)
        d = dto.to_dict()
        assert d["name"] == "ScoringEngine"
        assert d["confidence"] == 0.8

    def test_confidence_aggregation_to_dict(self):
        dto = ConfidenceAggregationDTO(source_name="Test", raw_confidence=0.7, weighted_confidence=0.7, weight=1.0)
        d = dto.to_dict()
        assert d["source_name"] == "Test"

    def test_conflict_resolution_to_dict(self):
        dto = ConflictResolutionDTO(source_a="A", source_b="B", value_a=0.9, value_b=0.3, resolved_value=0.6, resolution_strategy="average")
        d = dto.to_dict()
        assert d["resolution_strategy"] == "average"

    def test_consensus_score_to_dict(self):
        dto = ConsensusScoreDTO(final_score=0.75, agreement_level="strong", source_count=3)
        d = dto.to_dict()
        assert d["final_score"] == 0.75

    def test_source_priority_to_dict(self):
        dto = SourcePriorityDTO(source_name="Test", priority=1, weight=1.0, is_active=True)
        d = dto.to_dict()
        assert d["is_active"] is True

    def test_recommendation_ranking_to_dict(self):
        dto = RecommendationRankingDTO(rank=1, signal_id=1, symbol="BTCUSDT", composite_score=0.85, recommendation="STRONG_BUY")
        d = dto.to_dict()
        assert d["recommendation"] == "STRONG_BUY"

    def test_coordinator_diagnostics_to_dict(self):
        dto = CoordinatorDiagnosticsDTO(total_evaluations=10, avg_processing_time_ms=50.0, uptime_seconds=3600.0)
        d = dto.to_dict()
        assert d["total_evaluations"] == 10

    def test_coordinator_report_to_dict(self):
        dto = CoordinatorReportDTO(
            consensus=ConsensusScoreDTO(final_score=0.75),
            aggregations=[ConfidenceAggregationDTO(source_name="A", raw_confidence=0.7, weighted_confidence=0.7, weight=1.0)],
        )
        d = dto.to_dict()
        assert d["consensus"]["final_score"] == 0.75
        assert len(d["aggregations"]) == 1


class TestIntelligenceRegistry:

    def test_register_and_list(self):
        registry = IntelligenceRegistry()
        registry.register("TestSource", "scoring", instance="instance", weight=1.0, priority=5)
        sources = registry.list_sources()
        assert len(sources) == 1
        assert sources[0]["name"] == "TestSource"
        assert sources[0]["source_type"] == "scoring"

    def test_register_multiple(self):
        registry = IntelligenceRegistry()
        registry.register("A", "scoring", instance=None)
        registry.register("B", "intelligence", instance=None)
        assert registry.count == 2

    def test_unregister(self):
        registry = IntelligenceRegistry()
        registry.register("Test", "scoring", instance=None)
        assert registry.count == 1
        registry.unregister("Test")
        assert registry.count == 0

    def test_get_instance(self):
        registry = IntelligenceRegistry()
        registry.register("Test", "scoring", instance="my_instance")
        assert registry.get_instance("Test") == "my_instance"
        assert registry.get_instance("Nonexistent") is None

    def test_mark_error(self):
        registry = IntelligenceRegistry()
        registry.register("Test", "scoring", instance=None)
        registry.mark_error("Test")
        sources = registry.list_sources()
        assert sources[0]["error_count"] == 1


class TestAISourceRegistry:

    def test_register_and_priorities(self):
        registry = AISourceRegistry()
        registry.register("Scoring", weight=1.0, priority=5)
        registry.register("Intelligence", weight=0.8, priority=3)
        priorities = registry.get_priorities()
        assert len(priorities) == 2
        assert priorities[0].source_name == "Scoring"  # higher priority first

    def test_set_active(self):
        registry = AISourceRegistry()
        registry.register("Test", weight=1.0, priority=5)
        registry.set_active("Test", False)
        priorities = registry.get_priorities()
        assert priorities[0].is_active is False

    def test_list_sources(self):
        registry = AISourceRegistry()
        registry.register("Test", version="2.0", capabilities=["scoring", "ranking"])
        sources = registry.list_sources()
        assert len(sources) == 1
        assert "capabilities" in sources[0]


class TestCoordinatorService:

    def test_evaluate_no_sources(self):
        coordinator = CoordinatorService()
        signal = FakeSignal()
        report = coordinator.evaluate(signal)

        assert report.consensus is not None
        assert report.consensus.final_score == 0.0
        assert report.aggregations == []
        assert report.conflicts == []
        assert report.diagnostics is not None
        assert report.diagnostics.total_evaluations == 1

    def test_evaluate_with_registered_sources(self):
        coordinator = CoordinatorService()
        coordinator.intelligence_registry.register("SourceA", "scoring", instance=None, weight=1.0)
        coordinator.intelligence_registry.register("SourceB", "scoring", instance=None, weight=0.5)

        signal = FakeSignal()
        scores = {"final_score": 0.85}
        report = coordinator.evaluate(signal, scores)

        assert report.consensus is not None
        assert len(report.aggregations) == 2
        assert report.consensus.source_count == 2
        assert report.diagnostics.total_evaluations == 1

    def test_conflict_detection(self):
        coordinator = CoordinatorService()
        coordinator.intelligence_registry.register("SourceA", "scoring", instance=None, weight=1.0)
        coordinator.intelligence_registry.register("SourceB", "scoring", instance=None, weight=1.0)

        class HighSource:
            def score(self, signal):
                return {"final_score": 0.9}

        class LowSource:
            def score(self, signal):
                return {"final_score": 0.2}

        coordinator.intelligence_registry._sources["SourceA"]["instance"] = HighSource()
        coordinator.intelligence_registry._sources["SourceB"]["instance"] = LowSource()

        signal = FakeSignal()
        report = coordinator.evaluate(signal, {"final_score": 0.9})

        assert len(report.conflicts) > 0

    def test_consensus_agreement_strong(self):
        coordinator = CoordinatorService()
        coordinator.intelligence_registry.register("A", "scoring", instance=None, weight=1.0)
        coordinator.intelligence_registry.register("B", "scoring", instance=None, weight=1.0)

        signal = FakeSignal()
        scores = {"final_score": 0.8}
        report = coordinator.evaluate(signal, scores)

        assert report.consensus.agreement_level == "strong"

    def test_recommendation_ranking(self):
        coordinator = CoordinatorService()
        signal = FakeSignal()
        report = coordinator.evaluate(signal)

        assert len(report.recommendations) > 0
        assert report.recommendations[0].signal_id == 1
        assert report.recommendations[0].symbol == "BTCUSDT"

    def test_diagnostics_tracking(self):
        coordinator = CoordinatorService()
        for _ in range(5):
            coordinator.evaluate(FakeSignal())

        diag = coordinator._build_diagnostics()
        assert diag.total_evaluations == 5
        assert diag.avg_processing_time_ms > 0

    def test_multiple_evaluations(self):
        coordinator = CoordinatorService()
        for i in range(3):
            report = coordinator.evaluate(FakeSignal(sid=i + 1))
            assert report.diagnostics.total_evaluations == i + 1
