from dataclasses import asdict

from fastapi import APIRouter, Request

from api.dependencies import require_user_id
from portfolio_engine import PortfolioEngine

router = APIRouter()


@router.get("/portfolio")
def get_portfolio(request: Request):
    user_id = require_user_id(request)
    stats = PortfolioEngine().stats(user_id=user_id)
    return asdict(stats)
