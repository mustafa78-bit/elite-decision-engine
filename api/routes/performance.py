from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas import PerformanceResponse

router = APIRouter(tags=["performance"])


@router.get("/performance", response_model=PerformanceResponse)
async def get_performance(request: Request) -> PerformanceResponse:
    stats = request.app.state.performance_engine.stats()
    return PerformanceResponse(
        sharpe_ratio=stats.sharpe_ratio,
        sortino_ratio=stats.sortino_ratio,
        profit_factor=stats.profit_factor,
        expectancy=stats.expectancy,
        recovery_factor=stats.recovery_factor,
        calmar_ratio=stats.calmar_ratio,
        average_r_multiple=stats.average_r_multiple,
        average_holding_hours=stats.average_holding_hours,
        consecutive_wins=stats.consecutive_wins,
        consecutive_losses=stats.consecutive_losses,
        best_trade=stats.best_trade,
        worst_trade=stats.worst_trade,
    )
