from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.counterfactual_service import CounterfactualService

router = APIRouter(prefix="/api/v1/counterfactuals")


class CounterfactualResponse(BaseModel):
    id: int
    trade_id: int
    actual_pnl: float
    no_trade_delta: float
    half_size_pnl: float
    tight_stop_pnl: float
    split_tp_pnl: float
    delayed_entry_pnl: float
    optimal_scenario: str
    optimal_potential_pnl: float


def _get_counterfactual_service() -> CounterfactualService:
    return CounterfactualService()


@router.post("/{trade_id}", response_model=CounterfactualResponse)
def analyze_trade(trade_id: int, user_id: int = 1):
    svc = _get_counterfactual_service()
    try:
        analysis = svc.analyze_counterfactuals(trade_id, user_id)
        return CounterfactualResponse(
            id=analysis.id,
            trade_id=analysis.trade_id,
            actual_pnl=analysis.actual_pnl,
            no_trade_delta=analysis.no_trade_delta,
            half_size_pnl=analysis.half_size_pnl,
            tight_stop_pnl=analysis.tight_stop_pnl,
            split_tp_pnl=analysis.split_tp_pnl,
            delayed_entry_pnl=analysis.delayed_entry_pnl,
            optimal_scenario=analysis.optimal_scenario,
            optimal_potential_pnl=analysis.optimal_potential_pnl,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.get("/{trade_id}", response_model=CounterfactualResponse)
def get_trade_analysis(trade_id: int, user_id: int = 1):
    # Retrieve or run analysis
    return analyze_trade(trade_id, user_id)
