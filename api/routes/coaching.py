from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.coaching_service import CoachingService

router = APIRouter(prefix="/api/v1/coaching")


class CoachingRecommendationResponse(BaseModel):
    id: int
    user_id: int
    category: str
    feedback: str
    related_bias_ids: List[int]
    related_trade_ids: List[int]
    suggested_action: str
    dismissed: bool


def _get_coaching_service() -> CoachingService:
    return CoachingService()


@router.get("", response_model=List[CoachingRecommendationResponse])
def get_coaching_recommendations(user_id: int = 1):
    svc = _get_coaching_service()
    try:
        recs = svc.get_recommendations(user_id)
        return [
            CoachingRecommendationResponse(
                id=r["id"],
                user_id=r["user_id"],
                category=r["category"],
                feedback=r["feedback"],
                related_bias_ids=r["related_bias_ids"],
                related_trade_ids=r["related_trade_ids"],
                suggested_action=r["suggested_action"],
                dismissed=r["dismissed"]
            )
            for r in recs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch coaching recommendations: {e}")
