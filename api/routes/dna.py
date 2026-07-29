from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, List

from services.dna_service import DecisionDNAService

router = APIRouter(prefix="/api/v1/dna")


class DNAResponse(BaseModel):
    user_id: int
    risk_profile: str
    decision_speed_seconds: float
    average_holding_duration_seconds: float
    preferred_market_regimes: List[str]
    preferred_strategies: List[str]
    win_loss_ratio: float
    confidence_calibration_score: float
    trading_discipline_score: float
    behavioral_tendencies: dict


def _get_dna_service() -> DecisionDNAService:
    return DecisionDNAService()


@router.get("", response_model=DNAResponse)
def get_dna_profile(user_id: int = 1):
    svc = _get_dna_service()
    try:
        profile = svc.get_or_create_profile(user_id)
        return DNAResponse(
            user_id=profile["user_id"],
            risk_profile=profile["risk_profile"],
            decision_speed_seconds=profile["decision_speed_seconds"],
            average_holding_duration_seconds=profile["average_holding_duration_seconds"],
            preferred_market_regimes=profile["preferred_market_regimes"],
            preferred_strategies=profile["preferred_strategies"],
            win_loss_ratio=profile["win_loss_ratio"],
            confidence_calibration_score=profile["confidence_calibration_score"],
            trading_discipline_score=profile["trading_discipline_score"],
            behavioral_tendencies=profile["behavioral_tendencies"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DNA profile: {e}")


@router.post("/rebuild", response_model=DNAResponse)
def rebuild_dna_profile(user_id: int = 1):
    svc = _get_dna_service()
    try:
        profile = svc.update_profile_from_history(user_id)
        return DNAResponse(
            user_id=profile["user_id"],
            risk_profile=profile["risk_profile"],
            decision_speed_seconds=profile["decision_speed_seconds"],
            average_holding_duration_seconds=profile["average_holding_duration_seconds"],
            preferred_market_regimes=profile["preferred_market_regimes"],
            preferred_strategies=profile["preferred_strategies"],
            win_loss_ratio=profile["win_loss_ratio"],
            confidence_calibration_score=profile["confidence_calibration_score"],
            trading_discipline_score=profile["trading_discipline_score"],
            behavioral_tendencies=profile["behavioral_tendencies"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild DNA profile: {e}")
