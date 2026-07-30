import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_session
from core.experience.service import (
    ExperienceSubstrateService,
    InstinctStateService,
    FamiliaritySignalService,
    ExperienceVsKnowledgeService,
    ExperienceSufficiencyService,
    ExperienceGraduationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/experience", tags=["Experience Engine"])


def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


# Pydantic Schemas for input validation

class FeatureSet(BaseModel):
    trend_score: float = Field(0.5, ge=0.0, le=1.0)
    volume_score: float = Field(0.5, ge=0.0, le=1.0)
    rsi: float = Field(50.0, ge=0.0, le=100.0)
    regime: str = Field("TREND")
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    score: float = Field(0.5, ge=0.0, le=1.0)


class ContrastRequest(BaseModel):
    symbol: str
    timeframe: str
    current_features: FeatureSet
    knowledge_score: float


class GovernanceApprovalRequest(BaseModel):
    symbol: str
    timeframe: str
    governor_name: str


class ProduceTestExperienceRequest(BaseModel):
    timestamp: str
    symbol: str
    timeframe: str
    state_snapshot: Dict[str, Any]
    action_taken: str
    outcome: Optional[float] = None
    realized_at: Optional[str] = None


# --- READ-ORIENTED ENDPOINTS ---

@router.get("/substrate", status_code=status.HTTP_200_OK)
def get_substrate(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve chronological walk-forward experience substrate entries up to a given time."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format for current_time")

    subs = ExperienceSubstrateService.get_historical_substrate(db, t, symbol, timeframe)
    return [
        {
            "id": s.id,
            "timestamp": s.timestamp.isoformat(),
            "symbol": s.symbol,
            "timeframe": s.timeframe,
            "state_snapshot": s.state_snapshot,
            "action_taken": s.action_taken,
            "outcome": s.outcome,
            "realized_at": s.realized_at.isoformat() if s.realized_at else None,
        }
        for s in subs
    ]


@router.get("/instinct", status_code=status.HTTP_200_OK)
def get_instinct(
    symbol: str = Query(..., description="Asset symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve distilled instinct state containing the continuously evolving behavioral disposition vector."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format for current_time")

    instinct = InstinctStateService.compute_and_update_instinct(db, symbol, timeframe, t)
    return {
        "id": instinct.id,
        "symbol": instinct.symbol,
        "timeframe": instinct.timeframe,
        "disposition_vector": instinct.disposition_vector,
        "win_rate": instinct.win_rate,
        "profit_factor": instinct.profit_factor,
        "total_trades": instinct.total_trades,
        "avg_pnl": instinct.avg_pnl,
        "vibe_score": instinct.vibe_score,
        "last_updated": instinct.last_updated.isoformat() if instinct.last_updated else None,
    }


@router.post("/familiarity", status_code=status.HTTP_200_OK)
def get_familiarity(
    symbol: str,
    timeframe: str,
    features: FeatureSet,
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Calculate the familiarity of current market features by consulting distilled instinct (no direct DB scan)."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format")

    fam = FamiliaritySignalService.calculate_familiarity(db, symbol, timeframe, features.model_dump(), t)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "familiarity_signal": fam,
        "consulted_instinct": True,
    }


@router.post("/contrast", status_code=status.HTTP_200_OK)
def get_contrast(
    req: ContrastRequest,
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Contrast pre-trained general knowledge vs empirical lived history. Kept as independent dimensions."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format")

    result = ExperienceVsKnowledgeService.contrast_experience_vs_knowledge(
        db, req.symbol, req.timeframe, req.current_features.model_dump(), req.knowledge_score, t
    )
    return result


@router.get("/sufficiency", status_code=status.HTTP_200_OK)
def get_sufficiency(
    symbol: str = Query(..., description="Asset symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Evaluate whether the chronological duration of lived experience is sufficient."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format")

    res = ExperienceSufficiencyService.check_sufficiency(db, symbol, timeframe, t)
    return res


@router.get("/graduation/recommendation", status_code=status.HTTP_200_OK)
def get_graduation_recommendation(
    symbol: str = Query(..., description="Asset symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve current graduation recommendation (does NOT activate rules automatically)."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format")

    rec = ExperienceGraduationService.evaluate_graduation_recommendation(db, symbol, timeframe, t)
    return {
        "id": rec.id,
        "symbol": rec.symbol,
        "timeframe": rec.timeframe,
        "status": rec.status,
        "graduated": rec.graduated,
        "recommended_at": rec.recommended_at.isoformat() if rec.recommended_at else None,
        "graduated_at": rec.graduated_at.isoformat() if rec.graduated_at else None,
        "recommendation_payload": rec.recommendation_payload,
        "governance_rules": rec.governance_rules,
    }


# --- ACTIVE GOVERNANCE WRITE ACTIONS (Explicit Approvals) ---

@router.post("/governance/approve", status_code=status.HTTP_200_OK)
def approve_graduation_governance(
    req: GovernanceApprovalRequest,
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Explicit Governance Approval: Promotes the environment and activates multipliers."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format")

    grad = ExperienceGraduationService.approve_graduation(db, req.symbol, req.timeframe, req.governor_name, t)
    return {
        "message": "Graduation explicitly approved and rules activated under Governance",
        "symbol": grad.symbol,
        "timeframe": grad.timeframe,
        "status": grad.status,
        "graduated": grad.graduated,
        "governance_rules": grad.governance_rules,
    }


@router.post("/governance/reject", status_code=status.HTTP_200_OK)
def reject_graduation_governance(
    req: GovernanceApprovalRequest,
    current_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Explicit Governance Rejection/Revocation: Throttles or limits environment risk parameters."""
    try:
        t = datetime.fromisoformat(current_time) if current_time else datetime.now(timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format")

    grad = ExperienceGraduationService.reject_graduation(db, req.symbol, req.timeframe, req.governor_name, t)
    return {
        "message": "Graduation rejected/revoked by Governance",
        "symbol": grad.symbol,
        "timeframe": grad.timeframe,
        "status": grad.status,
        "graduated": grad.graduated,
        "governance_rules": grad.governance_rules,
    }


# --- CONTROLLED TESTING UTILITY ---

@router.post("/test-produce", status_code=status.HTTP_201_CREATED)
def test_produce_experience(
    req: ProduceTestExperienceRequest,
    db: Session = Depends(get_db),
):
    """Controlled testing utility to manually produce experience substrate entries (Mocking production of chronological living)."""
    try:
        ts = datetime.fromisoformat(req.timestamp)
        real_t = datetime.fromisoformat(req.realized_at) if req.realized_at else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    exp = ExperienceSubstrateService.record_experience(
        db, ts, req.symbol, req.timeframe, req.state_snapshot, req.action_taken, req.outcome, real_t
    )
    return {
        "message": "Experience produced successfully for testing",
        "substrate_id": exp.id,
    }
