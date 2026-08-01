from dataclasses import asdict

from fastapi import APIRouter

from performance_engine import PerformanceEngine


router = APIRouter()


@router.get("/performance")
def get_performance():
    stats = PerformanceEngine().stats()
    return asdict(stats)
