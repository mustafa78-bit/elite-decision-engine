from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import require_read
from dashboard.schemas import (
    ActivityResponse,
    OverviewResponse,
    PortfolioSummaryResponse,
    RiskSummaryResponse,
    StatsResponse,
)

router = APIRouter(
    tags=["dashboard"],
    dependencies=[Depends(require_read)],
)


@router.get("/dashboard/overview", response_model=OverviewResponse)
async def get_overview(request: Request) -> OverviewResponse:
    svc = request.app.state.dashboard_service
    svc._metrics.increment_requests()
    return svc.overview()


@router.get("/dashboard/stats", response_model=StatsResponse)
async def get_stats(request: Request) -> StatsResponse:
    svc = request.app.state.dashboard_service
    svc._metrics.increment_requests()
    return svc.stats()


@router.get("/dashboard/portfolio", response_model=PortfolioSummaryResponse)
async def get_portfolio(request: Request) -> PortfolioSummaryResponse:
    svc = request.app.state.dashboard_service
    svc._metrics.increment_requests()
    return svc.portfolio()


@router.get("/dashboard/risk", response_model=RiskSummaryResponse)
async def get_risk(request: Request) -> RiskSummaryResponse:
    svc = request.app.state.dashboard_service
    svc._metrics.increment_requests()
    return svc.risk()


@router.get("/dashboard/activity", response_model=ActivityResponse)
async def get_activity(request: Request) -> ActivityResponse:
    svc = request.app.state.dashboard_service
    svc._metrics.increment_requests()
    return svc.activity()
