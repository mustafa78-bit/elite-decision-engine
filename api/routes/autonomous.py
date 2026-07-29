from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from core.autonomous_models import IntelligenceContext
from core.autonomous_orchestrator import GlobalIntelligenceOrchestrator

router = APIRouter(prefix="/api/v1/autonomous")


class AutonomousOrchestrateRequest(BaseModel):
    symbol: str
    side: str
    user_id: int = 1
    stages: List[str]
    correlation_id: str = "corr_api"


class StageResultResponse(BaseModel):
    service_name: str
    status: str
    confidence: float
    reasoning: List[str]
    evidence: Dict[str, Any]
    supporting_signals: List[str]
    conflicting_signals: List[str]
    latency_ms: float
    metadata: Dict[str, Any]


class AutonomousOrchestrateResponse(BaseModel):
    correlation_id: str
    stages_completed: List[str]
    results: Dict[str, StageResultResponse]


def _get_orchestrator() -> GlobalIntelligenceOrchestrator:
    return GlobalIntelligenceOrchestrator()


@router.post("/orchestrate", response_model=AutonomousOrchestrateResponse)
def orchestrate_pipeline(body: AutonomousOrchestrateRequest):
    orchestrator = _get_orchestrator()
    try:
        # Build shared immutable context
        context = IntelligenceContext(
            symbol=body.symbol.upper(),
            side=body.side.upper(),
            user_id=body.user_id,
            correlation_id=body.correlation_id,
            market_state={"price": 50000.0, "regime": "TREND"}
        )

        pipeline_results = orchestrator.run_pipeline(context, body.stages)

        response_results = {}
        for k, v in pipeline_results.items():
            response_results[k] = StageResultResponse(
                service_name=v.service_name,
                status=v.status,
                confidence=v.confidence,
                reasoning=v.reasoning,
                evidence=v.evidence,
                supporting_signals=v.supporting_signals,
                conflicting_signals=v.conflicting_signals,
                latency_ms=v.latency_ms,
                metadata=v.metadata
            )

        return AutonomousOrchestrateResponse(
            correlation_id=body.correlation_id,
            stages_completed=body.stages,
            results=response_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration pipeline execution failed: {e}")
