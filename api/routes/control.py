from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas import StatusResponse

router = APIRouter(tags=["control"])


@router.get("/status", response_model=StatusResponse)
async def get_status(request: Request) -> StatusResponse:
    ks = request.app.state.kill_switch
    return StatusResponse(
        kill_switch=ks.state().value,
        running=ks.is_running(),
        dry_run=request.app.state.dry_run,
        trading_mode=request.app.state.trading_mode,
    )


@router.post("/kill-switch")
async def post_kill_switch(request: Request) -> dict:
    request.app.state.kill_switch.disable()
    return {"status": "ok", "message": "KillSwitch disabled"}


@router.post("/resume")
async def post_resume(request: Request) -> dict:
    request.app.state.kill_switch.resume()
    return {"status": "ok", "message": "Engine resumed"}
