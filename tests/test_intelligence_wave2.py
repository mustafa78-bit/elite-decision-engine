from __future__ import annotations

import pytest
from typing import Any

from services.intelligence.context import UnifiedIntelligenceContext
from services.intelligence.bus import CrossServiceEventBus, PriorityResolver
from services.intelligence.registry import IntelligenceRegistry
from services.intelligence.ranker import OpportunityRankingEngine
from services.intelligence.orchestrator import IntelligenceOrchestrator
from services.intelligence.services import (
    DecisionMemoryIntegrationService,
    PatternDiscoveryIntegrationService,
    RiskEngineIntegrationService,
    AIDebateIntegrationService,
    CounterfactualIntegrationService,
    ConfidenceCalibrationIntegrationService,
)


def test_intelligence_registry_operations():
    registry = IntelligenceRegistry()

    svc_dna = DecisionMemoryIntegrationService()
    registry.register(svc_dna, version="1.2.0", enabled=True, dependencies={"cache": True})

    assert registry.is_enabled("decision_memory") is True
    assert registry.get_service("decision_memory") == svc_dna

    # Toggle enabled state
    registry.set_enabled("decision_memory", False)
    assert registry.is_enabled("decision_memory") is False
    assert len(registry.get_active_services()) == 0

    registry.set_enabled("decision_memory", True)
    assert len(registry.get_active_services()) == 1

    # Health reporting
    registry.report_health("decision_memory", "SUCCESS")
    registry.report_health("decision_memory", "DEGRADED")
    registry.report_health("decision_memory", "CIRCUIT_BROKEN")

    report = registry.get_health_report()
    assert report["decision_memory"]["version"] == "1.2.0"
    assert report["decision_memory"]["health"]["invocations"] == 3
    assert report["decision_memory"]["health"]["successes"] == 1
    assert report["decision_memory"]["health"]["failures"] == 1


def test_opportunity_ranking_engine_calculation():
    engine = OpportunityRankingEngine()
    ctx = UnifiedIntelligenceContext()

    # Simulate empty/unpopulated parameters (neutral fallbacks)
    score_neutral = engine.calculate_score(ctx)
    # Default outputs should reside within normal bounds [0.0 - 100.0]
    assert 0.0 <= score_neutral <= 100.0

    # Populated bullish parameters
    ctx.pattern.pattern_score = 95.0
    ctx.risk.risk_score = 10.0  # low risk is better
    ctx.decision_memory.success_rate_matched = 85.0
    ctx.debate.council_consensus = 90.0
    ctx.counterfactual.expected_value_delta = 15.0  # EV delta 15.0 * 5.0 = 75.0 opportunity
    ctx.calibration.expected_calibration_error = 0.02  # ECE 0.02 -> 100.0 - 4.0 = 98.0 calibration score
    ctx.drift.psi_score = 0.05  # PSI 0.05 -> 100.0 - 15.0 = 85.0 drift score

    score_bullish = engine.calculate_score(ctx)
    assert score_bullish > score_neutral
    assert 0.0 <= score_bullish <= 100.0


def test_pipeline_metrics_and_extended_events_propagation():
    bus = CrossServiceEventBus()
    emitted_events = {}

    def capture_event(payload: Any, ctx: UnifiedIntelligenceContext):
        # Store payload under event type
        # Using a simplistic mock that logs which handler was invoked
        pass

    # Subscribe specific callbacks for extended events
    events_to_track = [
        "MemoryMatched", "PatternMatched", "DebateCompleted",
        "CounterfactualCompleted", "ConfidenceCalculated",
        "OpportunityRanked", "RecommendationGenerated",
        "pipeline_completed"
    ]

    for evt in events_to_track:
        # Bind using closure to record emitted topics
        def make_cb(name=evt):
            return lambda payload, ctx: emitted_events.update({name: payload})
        bus.subscribe(evt, make_cb())

    # Build services and register to orchestrator
    services = [
        DecisionMemoryIntegrationService(),
        PatternDiscoveryIntegrationService(),
        RiskEngineIntegrationService(),
        AIDebateIntegrationService(),
        CounterfactualIntegrationService(),
        ConfidenceCalibrationIntegrationService(),
    ]

    orchestrator = IntelligenceOrchestrator(services=services, event_bus=bus)

    # Execute pipeline on high-price BTC (Bullish patterns, memory matched)
    context = orchestrator.execute("BTC", 55000.0)

    # Verify that all integrated services completed successfully
    for svc in services:
        assert context.service_states[svc.get_service_name()] == "SUCCESS"

    # Verify extended events were triggered on the event bus
    for evt in events_to_track:
        assert evt in emitted_events, f"Event {evt} was not published!"

    # Verify values inside emitted events
    assert emitted_events["MemoryMatched"]["matches"] == 3
    assert emitted_events["PatternMatched"]["pattern"] == "Bullish Breakout Crossover"
    assert emitted_events["DebateCompleted"]["consensus"] == 78.5
    assert emitted_events["CounterfactualCompleted"]["best_action"] == "MARKET_BUY"
    assert emitted_events["ConfidenceCalculated"]["confidence"] > 0
    assert emitted_events["OpportunityRanked"]["score"] > 0
    assert emitted_events["RecommendationGenerated"]["symbol"] == "BTC"

    # Verify Pipeline Metrics
    metrics = context.pipeline_metrics
    assert metrics.pipeline_id == context.execution_id
    assert metrics.correlation_id == context.correlation_id
    assert metrics.total_latency_ms > 0
    assert len(metrics.per_service_latency_ms) == 6
    assert metrics.slowest_service in [s.get_service_name() for s in services]
    assert metrics.failure_count == 0
    assert len(metrics.memory_matches) == 3
    assert metrics.pattern_matches == ["Bullish Breakout Crossover"]
