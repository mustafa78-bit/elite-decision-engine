from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.strategic_intelligence_service import StrategicIntelligenceService

router = APIRouter(prefix="/api/v1/strategic-intelligence")


class StrategicAssessmentResponse(BaseModel):
    symbol: str
    user_id: int
    strategic_score: float
    recommendations: List[str]
    dna_risk_profile: str
    consensus_score: float
    expected_reward_usd: float


def _get_strategic_service() -> StrategicIntelligenceService:
    return StrategicIntelligenceService()


@router.get("", response_model=StrategicAssessmentResponse)
def get_strategic_assessment(symbol: str = "BTC", user_id: int = 1):
    svc = _get_strategic_service()
    try:
        result = svc.generate_strategic_assessment(symbol=symbol.upper(), user_id=user_id)
        return StrategicAssessmentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate strategic assessment: {e}")
