from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from services.watchlist_service import WatchlistService

router = APIRouter()


def _get_watchlist_service() -> WatchlistService:
    return WatchlistService()


@router.get("/watchlists")
def list_watchlists(request: Request):
    user_id = request.state.user_id
    svc = _get_watchlist_service()
    return {"watchlists": svc.list_watchlists(user_id=user_id)}


@router.get("/watchlists/{watchlist_id}")
def get_watchlist(watchlist_id: int, request: Request):
    svc = _get_watchlist_service()
    result = svc.get_watchlist(watchlist_id)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if result.get("user_id") is not None and result.get("user_id") != request.state.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this watchlist")
    return result


@router.post("/watchlists")
def create_watchlist(request: Request, name: str = "Default", symbols: str = ""):
    user_id = request.state.user_id
    svc = _get_watchlist_service()
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else []
    return svc.create_watchlist(name=name, symbols=symbol_list, user_id=user_id)


@router.put("/watchlists/{watchlist_id}")
def update_watchlist(watchlist_id: int, request: Request, data: dict = {}):
    svc = _get_watchlist_service()
    # Check permissions
    existing = svc.get_watchlist(watchlist_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if existing.get("user_id") is not None and existing.get("user_id") != request.state.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this watchlist")

    result = svc.update_watchlist(watchlist_id, data)
    return result


@router.delete("/watchlists/{watchlist_id}")
def delete_watchlist(watchlist_id: int, request: Request):
    svc = _get_watchlist_service()
    # Check permissions
    existing = svc.get_watchlist(watchlist_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if existing.get("user_id") is not None and existing.get("user_id") != request.state.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this watchlist")

    if not svc.delete_watchlist(watchlist_id):
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"success": True}


@router.post("/watchlists/{watchlist_id}/symbols")
def add_symbol_to_watchlist(watchlist_id: int, symbol: str, request: Request):
    svc = _get_watchlist_service()
    # Check permissions
    existing = svc.get_watchlist(watchlist_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if existing.get("user_id") is not None and existing.get("user_id") != request.state.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this watchlist")

    result = svc.add_symbol(watchlist_id, symbol)
    return result


@router.delete("/watchlists/{watchlist_id}/symbols/{symbol}")
def remove_symbol_from_watchlist(watchlist_id: int, symbol: str, request: Request):
    svc = _get_watchlist_service()
    # Check permissions
    existing = svc.get_watchlist(watchlist_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    if existing.get("user_id") is not None and existing.get("user_id") != request.state.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this watchlist")

    result = svc.remove_symbol(watchlist_id, symbol)
    return result
