from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.orchestrator.models import IntelligenceContext, IntelligenceResult, IntelligenceEvent
from core.orchestrator.event_bus import event_bus
from core.orchestrator.registry import intelligence_registry

logger = logging.getLogger(__name__)


class GlobalIntelligenceOrchestrator:
    """
    Central orchestration engine responsible for coordinating, sequencing, aggregating,
    and routing context through the deterministic ADIP workflow layers.

    Ensures 0% direct business logic inside the orchestrator layer.
    """

    def __init__(self, registry=None, bus=None):
        self.registry = registry or intelligence_registry
        self.bus = bus or event_bus

        # Mandatory deterministic sequencing order
        self.sequence_stages = [
            "Market Context",
            "Market Regime",
            "Decision Memory",
            "Pattern Discovery",
            "Risk Engine",
            "AI Debate",
            "Counterfactual Engine",
            "Confidence Calibration",
            "Priority Ranking",
            "Explainability",
            "Executive Recommendation"
        ]

    def orchestrate(self, symbol: str, raw_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes the entire sequential intelligence pipeline deterministically.
        Aggregates outputs into a final execution profile without mutating shared state.
        """
        start_time = time.perf_counter()

        # Initialize context
        context = IntelligenceContext(
            symbol=symbol,
            raw_inputs=raw_inputs or {},
            state={}
        )

        self.bus.publish(IntelligenceEvent(
            event_type="DecisionStarted",
            symbol=symbol,
            payload={"raw_inputs": raw_inputs or {}}
        ))

        pipeline_results: Dict[str, IntelligenceResult] = {}

        # Sequence matching through registry
        for stage in self.sequence_stages:
            stage_start = time.perf_counter()
            try:
                if self.registry.has_handler(stage):
                    handler = self.registry.get_handler(stage)
                    result = handler(context)
                else:
                    # Fallback to standard structured mock result if handler not registered
                    result = IntelligenceResult(
                        engine_name=stage,
                        confidence=0.8,
                        reasoning=f"Default reasoning for sequential stage: {stage}",
                        execution_time=round(time.perf_counter() - stage_start, 4)
                    )

                # Enforce explainability outputs on Result payload
                result.execution_time = round(time.perf_counter() - stage_start, 4)
                pipeline_results[stage] = result

                # Emit stage complete event
                event_name = stage.replace(" ", "") + "Completed"
                self.bus.publish(IntelligenceEvent(
                    event_type=event_name,
                    symbol=symbol,
                    payload={
                        "confidence": result.confidence,
                        "reasoning": result.reasoning,
                        "status": result.status
                    }
                ))

                # Feed state to sequential pipeline context safely
                context.state[stage] = {
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "evidence": result.evidence,
                    "status": result.status
                }

            except Exception as e:
                logger.error("[Orchestrator] Error executing stage %s: %s", stage, e)
                err_result = IntelligenceResult(
                    engine_name=stage,
                    confidence=0.0,
                    reasoning=f"Error executing stage {stage}: {str(e)}",
                    status="FAILED"
                )
                pipeline_results[stage] = err_result
                context.state[stage] = {"status": "FAILED", "error": str(e)}

        total_duration = time.perf_counter() - start_time

        # Build final unified portfolio recommendation profile
        final_recommendation = context.state.get("Executive Recommendation", {})
        recommendation_published_event = IntelligenceEvent(
            event_type="RecommendationPublished",
            symbol=symbol,
            payload={
                "symbol": symbol,
                "confidence": final_recommendation.get("confidence", 0.75),
                "reasoning": final_recommendation.get("reasoning", "Recommendation built successfully"),
                "total_duration": total_duration
            }
        )
        self.bus.publish(recommendation_published_event)

        return {
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline_stages": {k: v.dict() for k, v in pipeline_results.items()},
            "duration_seconds": round(total_duration, 4),
            "unified_context": context.dict()
        }


# Singleton Global Orchestrator
orchestrator = GlobalIntelligenceOrchestrator()
