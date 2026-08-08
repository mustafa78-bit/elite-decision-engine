from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from services.watchlist_service import WatchlistService

router = APIRouter()


def _get_watchlist_service() -> WatchlistService:
    return WatchlistService()


def _require_user_id(request: Request) -> int:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.get("/watchlists")
def list_watchlists(request: Request):
    user_id = _require_user_id(request)
    svc = _get_watchlist_service()
    return {"watchlists": svc.list_watchlists(user_id=user_id)}


@router.get("/watchlists/{watchlist_id}")
def get_watchlist(watchlist_id: int, request: Request):
    user_id = _require_user_id(request)
    svc = _get_watchlist_service()
    result = svc.get_watchlist(watchlist_id, user_id=user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.post("/watchlists")
def create_watchlist(request: Request, name: str = "Default", symbols: str = ""):
    user_id = _require_user_id(request)
    svc = _get_watchlist_service()
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else []
    return svc.create_watchlist(name=name, user_id=user_id, symbols=symbol_list)


@router.put("/watchlists/{watchlist_id}")
def update_watchlist(watchlist_id: int, request: Request, data: dict = {}):
    user_id = _require_user_id(request)
    svc = _get_watchlist_service()
    result = svc.update_watchlist(watchlist_id, user_id=user_id, data=data)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.delete("/watchlists/{watchlist_id}")
def delete_watchlist(watchlist_id: int, request: Request):
    user_id = _require_user_id(request)
    svc = _get_watchlist_service()
    if not svc.delete_watchlist(watchlist_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"success": True}


@router.post("/watchlists/{watchlist_id}/symbols")
def add_symbol_to_watchlist(watchlist_id: int, symbol: str, request: Request):
    user_id = _require_user_id(request)
    svc = _get_watchlist_service()
    result = svc.add_symbol(watchlist_id, user_id=user_id, symbol=symbol)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.delete("/watchlists/{watchlist_id}/symbols/{symbol}")
def remove_symbol_from_watchlist(watchlist_id: int, symbol: str, request: Request):
    user_id = _require_user_id(request)
    svc = _get_watchlist_service()
    result = svc.remove_symbol(watchlist_id, user_id=user_id, symbol=symbol)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result
