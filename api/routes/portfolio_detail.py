from __future__ import annotations

from fastapi import APIRouter, Query

from api.cache import cached
from services.portfolio_service import PortfolioService

router = APIRouter()


def _get_portfolio_service() -> PortfolioService:
    return PortfolioService()


@router.get("/portfolio/summary")
@cached(ttl=15)
def portfolio_summary():
    svc = _get_portfolio_service()
    return svc.summary()


@router.get("/portfolio/distribution")
@cached(ttl=15)
def portfolio_distribution():
    svc = _get_portfolio_service()
    return svc.distribution()


@router.get("/portfolio/performance")
@cached(ttl=30)
def portfolio_performance():
    svc = _get_portfolio_service()
    return svc.performance()


@router.get("/portfolio/risk")
@cached(ttl=15)
def portfolio_risk():
    svc = _get_portfolio_service()
    return svc.risk_metrics()


@router.get("/portfolio/full")
@cached(ttl=15)
def portfolio_full():
    svc = _get_portfolio_service()
    return svc.full_portfolio()
