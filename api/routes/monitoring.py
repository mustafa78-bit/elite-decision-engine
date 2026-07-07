from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import require_read

router = APIRouter(
    tags=["monitoring"],
    dependencies=[Depends(require_read)],
)


@router.get("/monitoring")
async def get_monitoring(request: Request) -> dict:
    svc = request.app.state.monitoring_service
    svc._metrics.increment_requests()
    return {
        "metrics": svc._metrics.snapshot(),
        "health": svc._health.summary(),
        "diagnostics": svc._diagnostics.runtime_summary(),
    }


@router.get("/monitoring/health")
async def get_monitoring_health(request: Request) -> dict:
    svc = request.app.state.monitoring_service
    svc._metrics.increment_requests()
    return svc._health.summary()


@router.get("/monitoring/metrics")
async def get_monitoring_metrics(request: Request) -> dict:
    svc = request.app.state.monitoring_service
    svc._metrics.increment_requests()
    return svc._metrics.snapshot()


@router.get("/monitoring/diagnostics")
async def get_monitoring_diagnostics(request: Request) -> dict:
    svc = request.app.state.monitoring_service
    svc._metrics.increment_requests()
    return svc._diagnostics.runtime_summary()
