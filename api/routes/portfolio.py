from dataclasses import asdict

from fastapi import APIRouter

from portfolio_engine import PortfolioEngine


router = APIRouter()


@router.get("/portfolio")
def get_portfolio():
    stats = PortfolioEngine().stats()
    return asdict(stats)
