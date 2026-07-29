from __future__ import annotations

import logging
import time
from typing import Any, List, Dict

from core.autonomous_models import (
    IntelligenceContext,
    IntelligenceResult,
    PipelineStarted,
    ServiceStarted,
    ServiceCompleted,
    ServiceFailed,
    PipelineCompleted
)
from core.intelligence_registry import IntelligenceRegistry
from core.autonomous_event_bus import AutonomousEventBus

logger = logging.getLogger(__name__)


class GlobalIntelligenceOrchestrator:
    def __init__(self):
        self.registry = IntelligenceRegistry()
        self.event_bus = AutonomousEventBus()

    def run_pipeline(
        self,
        context: IntelligenceContext,
        pipeline_stages: List[str]
    ) -> Dict[str, IntelligenceResult]:

        correlation_id = context.correlation_id
        start_time = time.perf_counter()

        # Publish PipelineStarted
        self.event_bus.publish(PipelineStarted(correlation_id=correlation_id))
        logger.info("TELEMETRY: [AutonomousOrchestrator] Starting autonomous intelligence pipeline %s", correlation_id)

        results: Dict[str, IntelligenceResult] = {}

        for stage in pipeline_stages:
            stage_start = time.perf_counter()
            self.event_bus.publish(ServiceStarted(correlation_id=correlation_id, service_name=stage))

            service_callable = self.registry.get_service(stage)
            if not service_callable:
                # Service not registered, emit failure and skip
                duration = (time.perf_counter() - stage_start) * 1000.0
                results[stage] = IntelligenceResult(
                    service_name=stage,
                    status="SKIPPED",
                    confidence=0.0,
                    reasoning=[f"Service {stage} not registered in registry."],
                    latency_ms=duration
                )
                self.event_bus.publish(ServiceFailed(
                    correlation_id=correlation_id,
                    service_name=stage,
                    error_message=f"Service {stage} not found in registry",
                    duration_ms=duration
                ))
                continue

            try:
                # Execute service call with context
                res_dict = service_callable(context)
                duration = (time.perf_counter() - stage_start) * 1000.0

                results[stage] = IntelligenceResult(
                    service_name=stage,
                    status="SUCCESS",
                    confidence=float(res_dict.get("confidence", 80.0)),
                    reasoning=res_dict.get("reasoning", []),
                    evidence=res_dict.get("evidence", {}),
                    supporting_signals=res_dict.get("supporting_signals", []),
                    conflicting_signals=res_dict.get("conflicting_signals", []),
                    latency_ms=duration,
                    metadata=res_dict.get("metadata", {})
                )

                self.event_bus.publish(ServiceCompleted(
                    correlation_id=correlation_id,
                    service_name=stage,
                    status="SUCCESS",
                    duration_ms=duration
                ))

            except Exception as e:
                duration = (time.perf_counter() - stage_start) * 1000.0
                results[stage] = IntelligenceResult(
                    service_name=stage,
                    status="FAILURE",
                    confidence=0.0,
                    reasoning=[f"Execution failed: {e}"],
                    latency_ms=duration
                )
                self.event_bus.publish(ServiceFailed(
                    correlation_id=correlation_id,
                    service_name=stage,
                    error_message=str(e),
                    duration_ms=duration
                ))
                logger.error("TELEMETRY: [AutonomousOrchestrator] Service %s execution failed: %s", stage, e)

        # Publish PipelineCompleted
        total_duration = (time.perf_counter() - start_time) * 1000.0
        self.event_bus.publish(PipelineCompleted(
            correlation_id=correlation_id,
            status="SUCCESS",
            duration_ms=total_duration
        ))

        logger.info(
            "TELEMETRY: [AutonomousOrchestrator] Completed autonomous pipeline %s in %s ms",
            correlation_id, round(total_duration, 2)
        )

        return results
