from dataclasses import asdict

from fastapi import APIRouter, Request

from api.dependencies import require_user_id
from performance_engine import PerformanceEngine

router = APIRouter()


@router.get("/performance")
def get_performance(request: Request):
    user_id = require_user_id(request)
    stats = PerformanceEngine().stats(user_id=user_id)
    return asdict(stats)
