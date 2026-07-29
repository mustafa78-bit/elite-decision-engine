from __future__ import annotations

import time
import pytest
from typing import Any

from services.intelligence.context import UnifiedIntelligenceContext
from services.intelligence.bus import (
    IntelligenceServiceContract,
    CrossServiceEventBus,
    PriorityResolver,
)
from services.intelligence.orchestrator import IntelligenceOrchestrator


class MockIntelligenceService:
    def __init__(self, name: str, priority: int, fail: bool = False, run_cb: Any = None):
        self.name = name
        self.priority = priority
        self.fail = fail
        self.run_cb = run_cb

    def get_service_name(self) -> str:
        return self.name

    def get_priority(self) -> int:
        return self.priority

    def run(self, context: UnifiedIntelligenceContext) -> Any:
        if self.fail:
            raise ValueError(f"Simulated failure for service: {self.name}")
        if self.run_cb:
            self.run_cb(context)


def test_unified_intelligence_context_initialization():
    ctx = UnifiedIntelligenceContext(symbol="ETH", market_price=1850.5)
    assert ctx.symbol == "ETH"
    assert ctx.market_price == 1850.5
    assert ctx.execution_id is not None
    assert len(ctx.service_states) == 0


def test_cross_service_event_bus_pub_sub():
    bus = CrossServiceEventBus()
    received_payloads = []

    def test_callback(payload: Any, ctx: UnifiedIntelligenceContext):
        received_payloads.append(payload)

    bus.subscribe("test_topic", test_callback)

    ctx = UnifiedIntelligenceContext()
    bus.publish("test_topic", {"data": "hello"}, ctx)

    assert received_payloads == [{"data": "hello"}]

    # Unsubscribe
    bus.unsubscribe("test_topic", test_callback)
    bus.publish("test_topic", {"data": "world"}, ctx)
    assert len(received_payloads) == 1


def test_priority_resolver_ordering():
    resolver = PriorityResolver(override_priorities={"service_b": 99})

    svc_a = MockIntelligenceService("service_a", priority=10)
    svc_b = MockIntelligenceService("service_b", priority=5)
    svc_c = MockIntelligenceService("service_c", priority=50)

    sorted_services = resolver.resolve([svc_a, svc_b, svc_c])

    # Expected: service_b (priority 99), service_c (priority 50), service_a (priority 10)
    assert [s.get_service_name() for s in sorted_services] == ["service_b", "service_c", "service_a"]


def test_orchestrator_execution_pipeline_success():
    bus = CrossServiceEventBus()
    events = []

    def log_event(payload, ctx):
        events.append(payload)

    bus.subscribe("service_success", log_event)

    def run_dna(ctx):
        ctx.dna.decision_dna_score = 85.0
        ctx.dna.traits = ["aggressive", "momentum_buyer"]

    def run_risk(ctx):
        ctx.risk.risk_score = 15.0
        ctx.risk.allowed = True

    svc_dna = MockIntelligenceService("decision_dna", priority=10, run_cb=run_dna)
    svc_risk = MockIntelligenceService("risk_engine", priority=20, run_cb=run_risk)

    orchestrator = IntelligenceOrchestrator(services=[svc_dna, svc_risk], event_bus=bus)
    context = orchestrator.execute("BTC", 30000.0)

    # Check state and context mutated by callback run methods
    assert context.service_states["decision_dna"] == "SUCCESS"
    assert context.service_states["risk_engine"] == "SUCCESS"
    assert context.dna.decision_dna_score == 85.0
    assert context.risk.risk_score == 15.0

    # Timing metrics should be populated
    assert "decision_dna" in context.timings
    assert "risk_engine" in context.timings
    assert "total_coordination" in context.timings

    # Confirm events captured
    assert len(events) == 2


def test_orchestrator_execution_pipeline_failure_fallback():
    svc_fail = MockIntelligenceService("failing_service", priority=10, fail=True)
    orchestrator = IntelligenceOrchestrator(services=[svc_fail])

    context = orchestrator.execute("BTC", 30000.0)

    # State should reflect DEGRADED instead of throwing exception
    assert context.service_states["failing_service"] == "DEGRADED"


def test_orchestrator_circuit_breaker_tripping():
    svc_fail = MockIntelligenceService("faulty_service", priority=10, fail=True)
    orchestrator = IntelligenceOrchestrator(services=[svc_fail])

    # Run 1: Failure 1
    ctx = orchestrator.execute("BTC", 30000.0)
    assert ctx.service_states["faulty_service"] == "DEGRADED"

    # Run 2: Failure 2
    ctx = orchestrator.execute("BTC", 30000.0)
    assert ctx.service_states["faulty_service"] == "DEGRADED"

    # Run 3: Failure 3 (Trips Circuit Breaker)
    ctx = orchestrator.execute("BTC", 30000.0)
    assert ctx.service_states["faulty_service"] == "DEGRADED"

    # Run 4: Bypassed/Circuit Broken
    ctx = orchestrator.execute("BTC", 30000.0)
    assert ctx.service_states["faulty_service"] == "CIRCUIT_BROKEN"


def test_orchestrator_global_metrics_computation():
    def run_dna(ctx):
        ctx.dna.decision_dna_score = 90.0

    def run_risk(ctx):
        ctx.risk.risk_score = 25.0

    def run_drift(ctx):
        ctx.drift.psi_score = 0.3  # Drift PSI

    svc_dna = MockIntelligenceService("decision_dna", priority=30, run_cb=run_dna)
    svc_risk = MockIntelligenceService("risk_engine", priority=20, run_cb=run_risk)
    svc_drift = MockIntelligenceService("drift_detection", priority=10, run_cb=run_drift)

    orchestrator = IntelligenceOrchestrator(services=[svc_dna, svc_risk, svc_drift])
    context = orchestrator.execute("BTC", 30000.0)

    # Overall Threat: min(100.0, max(risk_score=25.0, drift_psi=0.3 * 100.0 = 30.0)) -> 30.0
    assert context.metrics["overall_threat_score"] == 30.0

    # Aggregated Confidence: weighted average of success pathways
    assert context.metrics["aggregated_confidence"] == 90.0
