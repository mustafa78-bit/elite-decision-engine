from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.dqs_service import DQSService

router = APIRouter(prefix="/api/v1/dqs")


class DQSBreakdown(BaseModel):
    evidence_quality: float
    timing_accuracy: float
    risk_compliance: float
    execution_precision: float
    psychological_calibration: float
    discipline_index: float
    outcome_score: float


class DQSResponse(BaseModel):
    trade_id: int
    score: float
    breakdown: DQSBreakdown


def _get_dqs_service() -> DQSService:
    return DQSService()


@router.get("/{trade_id}", response_model=DQSResponse)
def get_dqs_score(trade_id: int):
    svc = _get_dqs_service()
    result = svc.calculate_dqs_for_trade(trade_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return DQSResponse(
        trade_id=result["trade_id"],
        score=result["score"],
        breakdown=DQSBreakdown(**result["breakdown"])
    )
