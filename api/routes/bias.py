from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.bias_service import CognitiveBiasService

router = APIRouter(prefix="/api/v1/biases")


class BiasResponse(BaseModel):
    id: int
    decision_id: int | None = None
    user_id: int
    bias_type: str
    confidence: float
    evidence: dict
    explanation: str
    suggested_improvement: str


def _get_bias_service() -> CognitiveBiasService:
    return CognitiveBiasService()


@router.get("", response_model=List[BiasResponse])
def get_cognitive_biases(user_id: int = 1):
    svc = _get_bias_service()
    try:
        logs = svc.get_logs_for_user(user_id)
        return [
            BiasResponse(
                id=log["id"],
                decision_id=log["decision_id"],
                user_id=log["user_id"],
                bias_type=log["bias_type"],
                confidence=log["confidence"],
                evidence=log["evidence"],
                explanation=log["explanation"],
                suggested_improvement=log["suggested_improvement"],
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cognitive biases: {e}")


@router.post("/detect/{trade_id}", response_model=List[BiasResponse])
def detect_biases(trade_id: int, user_id: int = 1):
    svc = _get_bias_service()
    try:
        logs = svc.detect_biases_for_trade(user_id, trade_id)
        return [
            BiasResponse(
                id=log["id"],
                decision_id=log["decision_id"],
                user_id=log["user_id"],
                bias_type=log["bias_type"],
                confidence=log["confidence"],
                evidence=log["evidence"],
                explanation=log["explanation"],
                suggested_improvement=log["suggested_improvement"],
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect cognitive biases: {e}")
