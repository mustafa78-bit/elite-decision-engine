from __future__ import annotations

from fastapi import APIRouter, Depends

from api.cache import cached
from api.dependencies import require_user_id
from services.portfolio_service import PortfolioService

router = APIRouter()


def _get_portfolio_service() -> PortfolioService:
    return PortfolioService()


@router.get("/portfolio/summary")
@cached(ttl=15)
def portfolio_summary(user_id: int = Depends(require_user_id)):
    svc = _get_portfolio_service()
    return svc.summary(user_id=user_id)


@router.get("/portfolio/distribution")
@cached(ttl=15)
def portfolio_distribution(user_id: int = Depends(require_user_id)):
    svc = _get_portfolio_service()
    return svc.distribution(user_id=user_id)


@router.get("/portfolio/performance")
@cached(ttl=30)
def portfolio_performance(user_id: int = Depends(require_user_id)):
    svc = _get_portfolio_service()
    return svc.performance(user_id=user_id)


@router.get("/portfolio/risk")
@cached(ttl=15)
def portfolio_risk(user_id: int = Depends(require_user_id)):
    svc = _get_portfolio_service()
    return svc.risk_metrics(user_id=user_id)


@router.get("/portfolio/full")
@cached(ttl=15)
def portfolio_full(user_id: int = Depends(require_user_id)):
    svc = _get_portfolio_service()
    return svc.full_portfolio(user_id=user_id)
