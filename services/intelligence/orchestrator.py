from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from services.intelligence.context import UnifiedIntelligenceContext
from services.intelligence.bus import (
    IntelligenceServiceContract,
    CrossServiceEventBus,
    PriorityResolver,
)

logger = logging.getLogger(__name__)


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
    ):
        self.services = services or []
        self.event_bus = event_bus or CrossServiceEventBus()
        self.priority_resolver = priority_resolver or PriorityResolver()

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

                self.event_bus.publish("service_success", {"service": name}, context)

            except Exception as e:
                logger.error("Failed executing intelligence service %s: %s", name, e, exc_info=True)
                context.service_states[name] = "DEGRADED"

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

        # Calculate a global threat score and confidence metric
        context.metrics["overall_threat_score"] = self._compute_overall_threat(context)
        context.metrics["aggregated_confidence"] = self._compute_aggregated_confidence(context)

        self.event_bus.publish("pipeline_completed", context.metrics, context)
        return context

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
        if context.service_states.get("calibration") == "SUCCESS":
            contributions.append(context.calibration.confidence_scale_factor * 100.0)
        if context.service_states.get("debate") == "SUCCESS":
            contributions.append(context.debate.council_consensus)

        if not contributions:
            return 50.0  # neutral fallback
        return sum(contributions) / len(contributions)
