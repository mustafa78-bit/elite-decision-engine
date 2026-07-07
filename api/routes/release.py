from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import require_read

router = APIRouter(
    tags=["release"],
    dependencies=[Depends(require_read)],
)


@router.get("/ready")
async def get_ready(request: Request) -> dict:
    return request.app.state.readiness_service.is_ready()


@router.get("/version")
async def get_version(request: Request) -> dict:
    return request.app.state.version_service.get_version()
