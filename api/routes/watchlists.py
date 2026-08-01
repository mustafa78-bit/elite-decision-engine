from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.watchlist_service import WatchlistService

router = APIRouter()


def _get_watchlist_service() -> WatchlistService:
    return WatchlistService()


@router.get("/watchlists")
def list_watchlists(user_id: Optional[int] = Query(None)):
    svc = _get_watchlist_service()
    return {"watchlists": svc.list_watchlists(user_id=user_id)}


@router.get("/watchlists/{watchlist_id}")
def get_watchlist(watchlist_id: int):
    svc = _get_watchlist_service()
    result = svc.get_watchlist(watchlist_id)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.post("/watchlists")
def create_watchlist(name: str = "Default", symbols: str = "", user_id: Optional[int] = Query(None)):
    svc = _get_watchlist_service()
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else []
    return svc.create_watchlist(name=name, symbols=symbol_list, user_id=user_id)


@router.put("/watchlists/{watchlist_id}")
def update_watchlist(watchlist_id: int, data: dict = {}):
    svc = _get_watchlist_service()
    result = svc.update_watchlist(watchlist_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.delete("/watchlists/{watchlist_id}")
def delete_watchlist(watchlist_id: int):
    svc = _get_watchlist_service()
    if not svc.delete_watchlist(watchlist_id):
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"success": True}


@router.post("/watchlists/{watchlist_id}/symbols")
def add_symbol_to_watchlist(watchlist_id: int, symbol: str):
    svc = _get_watchlist_service()
    result = svc.add_symbol(watchlist_id, symbol)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.delete("/watchlists/{watchlist_id}/symbols/{symbol}")
def remove_symbol_from_watchlist(watchlist_id: int, symbol: str):
    svc = _get_watchlist_service()
    result = svc.remove_symbol(watchlist_id, symbol)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result
