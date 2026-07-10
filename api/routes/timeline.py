from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.timeline_service import TimelineService

router = APIRouter()


def _get_timeline_service() -> TimelineService:
    return TimelineService()


@router.get("/timeline/signal/{signal_id}")
def get_signal_timeline(signal_id: int):
    svc = _get_timeline_service()
    events = svc.signal_timeline(signal_id)
    if not events:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"signal_id": signal_id, "events": events}


@router.get("/timeline/trade/{trade_id}")
def get_trade_timeline(trade_id: int):
    svc = _get_timeline_service()
    events = svc.trade_timeline(trade_id)
    if not events:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"trade_id": trade_id, "events": events}


@router.get("/timeline")
def get_global_timeline(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
):
    svc = _get_timeline_service()
    return svc.global_timeline(
        limit=limit, offset=offset,
        event_type=event_type, symbol=symbol,
    )
