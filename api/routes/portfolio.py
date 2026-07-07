from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import require_read
from api.schemas import PortfolioResponse

router = APIRouter(tags=["portfolio"], dependencies=[Depends(require_read)])


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(request: Request) -> PortfolioResponse:
    stats = request.app.state.portfolio_engine.stats()
    return PortfolioResponse(
        total_trades=stats.total_trades,
        open_trades=stats.open_trades,
        closed_trades=stats.closed_trades,
        winning_trades=stats.winning_trades,
        losing_trades=stats.losing_trades,
        win_rate=stats.win_rate,
        total_pnl=stats.total_pnl,
        daily_pnl=stats.daily_pnl,
        average_win=stats.average_win,
        average_loss=stats.average_loss,
        profit_factor=stats.profit_factor,
        max_drawdown=stats.max_drawdown,
        current_open_exposure=stats.current_open_exposure,
    )
