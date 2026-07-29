from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.debate_service import AIDebateService

router = APIRouter(prefix="/api/v1/debate")


class AIDebateRequest(BaseModel):
    symbol: str
    side: str
    user_id: int = 1


class AIDebateResponse(BaseModel):
    symbol: str
    consensus_score: float
    arguments: List[str]
    counterarguments: List[str]
    minority_opinion: str
    final_recommendation: str


def _get_debate_service() -> AIDebateService:
    return AIDebateService()


@router.post("", response_model=AIDebateResponse)
def run_debate(body: AIDebateRequest):
    svc = _get_debate_service()
    try:
        result = svc.run_debate(
            symbol=body.symbol.upper(),
            side=body.side.upper(),
            user_id=body.user_id,
        )
        return AIDebateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debate failed: {e}")
