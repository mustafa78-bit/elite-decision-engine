from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import require_admin, require_read
from api.schemas import StatusResponse

router = APIRouter(tags=["control"])


@router.get("/status", response_model=StatusResponse, dependencies=[Depends(require_read)])
async def get_status(request: Request) -> StatusResponse:
    ks = request.app.state.kill_switch
    return StatusResponse(
        kill_switch=ks.state().value,
        running=ks.is_running(),
        dry_run=request.app.state.dry_run,
        trading_mode=request.app.state.trading_mode,
    )


@router.post("/kill-switch", dependencies=[Depends(require_admin)])
async def post_kill_switch(request: Request) -> dict:
    request.app.state.kill_switch.disable()
    return {"status": "ok", "message": "KillSwitch disabled"}


@router.post("/resume", dependencies=[Depends(require_admin)])
async def post_resume(request: Request) -> dict:
    request.app.state.kill_switch.resume()
    return {"status": "ok", "message": "Engine resumed"}
