from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from services.temporary_watch_service import TemporaryWatchService

router = APIRouter()


def _get_service() -> TemporaryWatchService:
    return TemporaryWatchService()


@router.get("/watchlist/temporary")
def list_temporary_watches(request: Request):
    svc = _get_service()
    return {"watches": svc.list_active()}


@router.post("/watchlist/temporary")
def add_temporary_watch(request: Request, symbol: str, days: int = 7, note: str | None = None):
    if not symbol or not symbol.strip():
        raise HTTPException(status_code=400, detail="Symbol is required")
    if days <= 0:
        raise HTTPException(status_code=400, detail="days must be positive")
    svc = _get_service()
    return svc.add_symbol(symbol=symbol.strip(), days=days, note=note)


@router.delete("/watchlist/temporary/{symbol}")
def remove_temporary_watch(symbol: str, request: Request):
    svc = _get_service()
    if not svc.remove_symbol(symbol):
        raise HTTPException(status_code=404, detail="Symbol not found in temporary watch list")
    return {"success": True}
