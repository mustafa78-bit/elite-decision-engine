from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from services.simulator_service import DecisionSimulatorService

router = APIRouter(prefix="/api/v1/simulator")


class DecisionSimulationRequest(BaseModel):
    symbol: str
    side: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    user_id: int = 1


class AlternativeOutcome(BaseModel):
    scenario: str
    stop_loss: float | None = None
    take_profit: float | None = None
    expected_risk_usd: float | None = None
    expected_reward_usd: float | None = None
    probability: str


class DecisionSimulationResponse(BaseModel):
    symbol: str
    side: str
    expected_outcome: str
    confidence: float
    expected_risk_usd: float
    expected_reward_usd: float
    primary_risks: List[str]
    supporting_evidence: List[str]
    alternative_outcomes: List[AlternativeOutcome]
    risk_reward_ratio: float


def _get_simulator_service() -> DecisionSimulatorService:
    return DecisionSimulatorService()


@router.post("", response_model=DecisionSimulationResponse)
def simulate_decision(body: DecisionSimulationRequest):
    svc = _get_simulator_service()
    try:
        result = svc.simulate_decision(
            symbol=body.symbol.upper(),
            side=body.side.upper(),
            entry_price=body.entry_price,
            stop_loss=body.stop_loss,
            take_profit=body.take_profit,
            position_size=body.position_size,
            user_id=body.user_id,
        )
        return DecisionSimulationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")
