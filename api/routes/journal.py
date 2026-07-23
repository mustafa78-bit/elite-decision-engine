from datetime import datetime, timezone

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database import JournalEntry, get_session

logger = logging.getLogger(__name__)
router = APIRouter()


class JournalCreate(BaseModel):
    symbol: str
    side: str
    entry_price: float
    exit_price: float | None = None
    score: float = 0
    confidence: float = 0
    entry_reason: str = ""
    exit_reason: str | None = None
    notes: str | None = None
    result: str = "PENDING"
    pnl: float = 0
    signal_id: int | None = None
    trade_id: int | None = None


class JournalUpdate(BaseModel):
    exit_price: float | None = None
    exit_reason: str | None = None
    notes: str | None = None
    result: str | None = None
    pnl: float | None = None


@router.get("/journal")
def list_journal(limit: int = Query(100, ge=1, le=500)):
    session = get_session()
    try:
        rows = session.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).all()
    finally:
        session.close()

    return [
        {
            "id": j.id,
            "symbol": j.symbol,
            "side": j.side,
            "entry_price": j.entry_price,
            "exit_price": j.exit_price,
            "score": round(j.score, 3),
            "confidence": round(j.confidence, 2),
            "entry_reason": j.entry_reason,
            "exit_reason": j.exit_reason,
            "notes": j.notes,
            "result": j.result,
            "pnl": round(j.pnl, 2),
            "signal_id": j.signal_id,
            "trade_id": j.trade_id,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in rows
    ]


@router.post("/journal")
def create_journal(body: JournalCreate):
    session = get_session()
    try:
        entry = JournalEntry(
            symbol=body.symbol.upper(),
            side=body.side.upper(),
            entry_price=body.entry_price,
            exit_price=body.exit_price,
            score=body.score,
            confidence=body.confidence,
            entry_reason=body.entry_reason,
            exit_reason=body.exit_reason,
            notes=body.notes,
            result=body.result.upper() if body.result else "PENDING",
            pnl=body.pnl,
            signal_id=body.signal_id,
            trade_id=body.trade_id,
        )
        session.add(entry)
        session.commit()
        return {"id": entry.id}
    except Exception as e:
        session.rollback()
        logger.error("Failed to create journal entry: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create journal entry")
    finally:
        session.close()


@router.put("/journal/{entry_id}")
def update_journal(entry_id: int, body: JournalUpdate):
    session = get_session()
    try:
        entry = session.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
        if not entry:
            return {"error": f"Entry {entry_id} not found"}

        if body.exit_price is not None:
            entry.exit_price = body.exit_price
        if body.exit_reason is not None:
            entry.exit_reason = body.exit_reason
        if body.notes is not None:
            entry.notes = body.notes
        if body.result is not None:
            entry.result = body.result.upper()
        if body.pnl is not None:
            entry.pnl = body.pnl

        session.commit()
        return {"status": "updated"}
    except Exception as e:
        session.rollback()
        logger.error("Failed to update journal entry %s: %s", entry_id, e)
        raise HTTPException(status_code=500, detail="Failed to update journal entry")
    finally:
        session.close()


@router.delete("/journal/{entry_id}")
def delete_journal(entry_id: int):
    session = get_session()
    try:
        entry = session.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
        if not entry:
            return {"error": f"Entry {entry_id} not found"}

        session.delete(entry)
        session.commit()
        return {"status": "deleted"}
    except Exception as e:
        session.rollback()
        logger.error("Failed to delete journal entry %s: %s", entry_id, e)
        raise HTTPException(status_code=500, detail="Failed to delete journal entry")
    finally:
        session.close()
