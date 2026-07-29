from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from services.intelligence.context import UnifiedIntelligenceContext, PipelineMetrics
from services.intelligence.bus import (
    IntelligenceServiceContract,
    CrossServiceEventBus,
    PriorityResolver,
)
from services.intelligence.ranker import OpportunityRankingEngine

logger = logging.getLogger(__name__)

# Circular buffer timeline store for Wave 3 API retrievals to prevent memory leaks
_GLOBAL_TIMELINE: deque = deque(maxlen=1000)


def _timeline_logger_listener(event_type: str, payload: Any, context: UnifiedIntelligenceContext) -> None:
    """Listens globally to CrossServiceEventBus and captures formatted timeline events."""
    summary = ""
    if event_type == "pipeline_started":
        summary = f"Pipeline execution started for asset {context.symbol}."
    elif event_type == "MemoryMatched":
        summary = f"Identified {payload.get('matches', 0)} historical decision matches with average success of {payload.get('success_rate', 0.0)}%."
    elif event_type == "PatternMatched":
        summary = f"Matched technical pattern: '{payload.get('pattern')}' with score of {payload.get('score', 0.0)}."
    elif event_type == "DebateCompleted":
        summary = f"Council Debate finished with consensus score of {payload.get('consensus', 0.0)}%."
    elif event_type == "CounterfactualCompleted":
        summary = f"Counterfactual scenario simulated: best alternative action is '{payload.get('best_action')}'."
    elif event_type == "ConfidenceCalculated":
        summary = f"Consolidated decision confidence calculated: {payload.get('confidence', 0.0)}%."
    elif event_type == "OpportunityRanked":
        summary = f"Normalized Executive Opportunity Score computed: {payload.get('score', 0.0)}."
    elif event_type == "RecommendationGenerated":
        summary = f"Generated ultimate decision recommendation for symbol {payload.get('symbol')} with opportunity score of {payload.get('opportunity_score', 0.0)}."
    elif event_type == "pipeline_completed":
        summary = "Pipeline orchestration cycle finished successfully."
    else:
        summary = f"Event '{event_type}' emitted."

    event_item = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": context.correlation_id,
        "event_type": event_type,
        "summary": summary,
        "payload": payload,
        "symbol": context.symbol,
        "market_price": context.market_price,
    }
    _GLOBAL_TIMELINE.append(event_item)


class IntelligenceOrchestrator:
    """The central orchestration brain of NEXUS.

    Orchestrates execution sequences, emits real-time events via CrossServiceEventBus,
    and safely tracks state across all registered downstream services.
    """

    def __init__(
        self,
        services: Optional[List[IntelligenceServiceContract]] = None,
        event_bus: Optional[CrossServiceEventBus] = None,
        priority_resolver: Optional[PriorityResolver] = None,
        ranker: Optional[OpportunityRankingEngine] = None,
    ):
        self.services = services or []
        self.event_bus = event_bus or CrossServiceEventBus()
        self.priority_resolver = priority_resolver or PriorityResolver()
        self.ranker = ranker or OpportunityRankingEngine()

        # Connect our global timeline capture hook
        self.event_bus.register_global_listener(_timeline_logger_listener)

        # Circuit breaker state: Map of service name -> consecutive failure count
        self._consecutive_failures: Dict[str, int] = {}
        self._bypass_until: Dict[str, float] = {}

    def register_service(self, service: IntelligenceServiceContract) -> None:
        """Dynamically registers an intelligence subsystem service."""
        self.services.append(service)
        logger.info("Registered intelligence service: %s", service.get_service_name())

    def execute(self, symbol: str, market_price: float) -> UnifiedIntelligenceContext:
        """Executes the complete coordinated intelligence pipeline."""
        context = UnifiedIntelligenceContext(symbol=symbol, market_price=market_price)
        total_start = time.perf_counter()

        self.event_bus.publish("pipeline_started", {"symbol": symbol}, context)

        # 1. Resolve execution order
        resolved_services = self.priority_resolver.resolve(self.services)

        failures_count = 0

        # 2. Iterate through resolved services and execute
        for service in resolved_services:
            name = service.get_service_name()
            context.service_states[name] = "PENDING"

            # Check circuit breaker
            now = time.time()
            if name in self._bypass_until and now < self._bypass_until[name]:
                logger.warning("Service %s bypassed due to active circuit breaker.", name)
                context.service_states[name] = "CIRCUIT_BROKEN"
                self.event_bus.publish("service_bypassed", {"service": name}, context)
                continue

            service_start = time.perf_counter()
            self.event_bus.publish("service_started", {"service": name}, context)

            try:
                # Execute service logic
                service.run(context)
                context.service_states[name] = "SUCCESS"
                self._consecutive_failures[name] = 0  # reset failures

                # Publish extended domain events based on service completion
                self._publish_service_completion_events(name, context)

                self.event_bus.publish("service_success", {"service": name}, context)

            except Exception as e:
                logger.error("Failed executing intelligence service %s: %s", name, e, exc_info=True)
                context.service_states[name] = "DEGRADED"
                failures_count += 1

                # Update circuit breaker tracking
                failures = self._consecutive_failures.get(name, 0) + 1
                self._consecutive_failures[name] = failures
                if failures >= 3:
                    self._bypass_until[name] = now + 60.0
                    logger.critical("Circuit breaker tripped for service: %s. Bypassing for 60 seconds.", name)

                self.event_bus.publish("service_failed", {"service": name, "error": str(e)}, context)

            finally:
                duration_ms = (time.perf_counter() - service_start) * 1000.0
                context.timings[name] = round(duration_ms, 2)

        # Final aggregate and timing
        total_duration_ms = (time.perf_counter() - total_start) * 1000.0
        context.timings["total_coordination"] = round(total_duration_ms, 2)

        # 3. Calculate dynamic indicators
        context.metrics["overall_threat_score"] = self._compute_overall_threat(context)

        aggregated_conf = self._compute_aggregated_confidence(context)
        context.metrics["aggregated_confidence"] = aggregated_conf
        self.event_bus.publish("ConfidenceCalculated", {"confidence": aggregated_conf}, context)

        # 4. Compute Executive Opportunity score
        opportunity_score = self.ranker.calculate_score(context)
        context.metrics["executive_opportunity_score"] = opportunity_score
        self.event_bus.publish("OpportunityRanked", {"score": opportunity_score}, context)

        # Emit terminal Recommendation event
        self.event_bus.publish("RecommendationGenerated", {
            "symbol": symbol,
            "opportunity_score": opportunity_score,
            "confidence": aggregated_conf,
        }, context)

        # 5. Populate Pipeline Metrics
        self._populate_pipeline_metrics(context, total_duration_ms, failures_count)

        self.event_bus.publish("pipeline_completed", context.metrics, context)
        return context

    def _publish_service_completion_events(self, service_name: str, context: UnifiedIntelligenceContext) -> None:
        """Publishes specific intelligence events when a subsystem succeeds."""
        if service_name == "decision_memory" and context.decision_memory.matched_decisions:
            self.event_bus.publish("MemoryMatched", {
                "matches": len(context.decision_memory.matched_decisions),
                "success_rate": context.decision_memory.success_rate_matched,
            }, context)
        elif service_name == "pattern_discovery" and context.pattern.pattern_name:
            self.event_bus.publish("PatternMatched", {
                "pattern": context.pattern.pattern_name,
                "score": context.pattern.pattern_score,
            }, context)
        elif service_name == "ai_debate" and context.debate.arguments:
            self.event_bus.publish("DebateCompleted", {
                "consensus": context.debate.council_consensus,
                "arguments": context.debate.arguments,
            }, context)
        elif service_name == "counterfactual" and context.counterfactual.scenario_scores:
            self.event_bus.publish("CounterfactualCompleted", {
                "best_action": context.counterfactual.best_alternative_action,
                "expected_delta": context.counterfactual.expected_value_delta,
            }, context)

    def _populate_pipeline_metrics(self, context: UnifiedIntelligenceContext, total_latency_ms: float, failure_count: int) -> None:
        """Constructs detailed executing metadata metrics of the completed pipeline."""
        metrics = context.pipeline_metrics
        metrics.pipeline_id = context.execution_id
        metrics.correlation_id = context.correlation_id
        metrics.total_latency_ms = round(total_latency_ms, 2)
        metrics.per_service_latency_ms = {k: v for k, v in context.timings.items() if k != "total_coordination"}
        metrics.failure_count = failure_count

        # Find slowest service
        slowest_name = None
        slowest_time = -1.0
        for k, v in metrics.per_service_latency_ms.items():
            if v > slowest_time:
                slowest_time = v
                slowest_name = k
        metrics.slowest_service = slowest_name

        # Confidence distribution
        conf_dist = []
        if context.service_states.get("decision_dna") == "SUCCESS":
            conf_dist.append(context.dna.decision_dna_score)
        if context.service_states.get("ai_debate") == "SUCCESS":
            conf_dist.append(context.debate.council_consensus)
        metrics.confidence_distribution = conf_dist

        metrics.memory_matches = context.decision_memory.matched_decisions
        metrics.pattern_matches = [context.pattern.pattern_name] if context.pattern.pattern_name else []

    def _compute_overall_threat(self, context: UnifiedIntelligenceContext) -> float:
        """Derives a deterministic overall threat score [0.0 - 100.0] based on risk and drift indicators."""
        risk_score = context.risk.risk_score
        drift_psi = context.drift.psi_score
        # Calculate a weighted maximum threat
        return min(100.0, max(risk_score, drift_psi * 100.0))

    def _compute_aggregated_confidence(self, context: UnifiedIntelligenceContext) -> float:
        """Derives a weighted platform-wide confidence score based on various intelligence outputs."""
        contributions = []
        if context.service_states.get("decision_dna") == "SUCCESS":
            contributions.append(context.dna.decision_dna_score)
        if context.service_states.get("confidence_calibration") == "SUCCESS":
            contributions.append(context.calibration.confidence_scale_factor * 100.0)
        if context.service_states.get("ai_debate") == "SUCCESS":
            contributions.append(context.debate.council_consensus)

        if not contributions:
            return 50.0  # neutral fallback
        return sum(contributions) / len(contributions)
