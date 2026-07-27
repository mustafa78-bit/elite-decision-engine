from dataclasses import asdict

from fastapi import APIRouter

from portfolio.engine import PortfolioEngine
from performance.engine import PerformanceEngine


router = APIRouter()


@router.get("/performance")
def get_performance():
    # Use consolidated modular performance report
    snapshot = PortfolioEngine().snapshot()
    report = PerformanceEngine().report(snapshot)
    return asdict(report)
