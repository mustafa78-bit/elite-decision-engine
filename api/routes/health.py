from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas import HealthCheckResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def get_health(request: Request) -> HealthCheckResponse:
    report = request.app.state.health_check.run()
    return HealthCheckResponse(
        overall=report.overall_status.value,
        duration_ms=report.duration_ms,
        checks={k: v.value for k, v in report.checks.items()},
        warnings=report.warnings,
        errors=report.errors,
    )
