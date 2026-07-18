from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from database import (
    FILLED,
    OPEN,
    PENDING,
    CANCEL,
    PARTIALLY_FILLED,
    TAKE_PROFIT,
    STOP_LOSS,
    CLOSED,
    PaperOrder as PaperOrderModel,
    PaperTrade as PaperTradeModel,
    Trade,
    get_session,
)

router = APIRouter()


def _serialize_order(o: PaperOrderModel) -> dict:
    return {
        "id": o.id,
        "symbol": o.symbol,
        "side": o.side,
        "order_type": o.order_type,
        "quantity": o.quantity,
        "price": o.price,
        "filled_price": o.filled_price,
        "filled_quantity": o.filled_quantity,
        "status": o.status,
        "trade_id": o.trade_id,
        "reason": o.reason,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }


def _serialize_trade(t: PaperTradeModel) -> dict:
    return {
        "id": t.id,
        "position_id": t.position_id,
        "order_id": t.order_id,
        "symbol": t.symbol,
        "side": t.side,
        "entry": t.entry,
        "exit_price": t.exit_price,
        "quantity": t.quantity,
        "pnl": t.pnl,
        "status": t.status,
        "close_reason": t.close_reason,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
    }


def _serialize_position(t: Trade) -> dict:
    return {
        "id": t.id,
        "symbol": t.symbol,
        "side": t.side,
        "entry": t.entry,
        "stop": t.stop,
        "tp1": t.tp1,
        "tp2": t.tp2,
        "status": t.status,
        "pnl": t.pnl,
        "exit_price": t.exit_price,
        "close_reason": t.close_reason,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
    }


def _apply_filters(query, model, symbol, status, side, date_from, date_to):
    if symbol is not None:
        query = query.filter(model.symbol == symbol.upper())
    if status is not None:
        query = query.filter(model.status == status.upper())
    if side is not None:
        query = query.filter(model.side == side.upper())
    if date_from is not None:
        try:
            dt = datetime.fromisoformat(date_from)
            query = query.filter(model.created_at >= dt)
        except ValueError:
            pass
    if date_to is not None:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.filter(model.created_at <= dt)
        except ValueError:
            pass
    return query


def _count_and_page(query, offset, limit):
    total = query.count()
    rows = query.order_by(PaperOrderModel.created_at.desc()).offset(offset).limit(limit).all()
    return rows, total


_VALID_ORDER_STATUSES = frozenset({PENDING, FILLED, PARTIALLY_FILLED, CANCEL})
_VALID_TRADE_STATUSES = frozenset({OPEN, TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL})
_VALID_SIDES = frozenset({"LONG", "SHORT"})


# ── Orders ─────────────────────────────────────────────────────────────────


@router.get("/paper/orders")
def list_orders(
    symbol: Optional[str] = Query(None, min_length=1, max_length=20),
    status: Optional[str] = Query(None, pattern="^(PENDING|FILLED|PARTIALLY_FILLED|CANCEL)$"),
    side: Optional[str] = Query(None, pattern="^(LONG|SHORT)$"),
    date_from: Optional[str] = Query(None, alias="date_from"),
    date_to: Optional[str] = Query(None, alias="date_to"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_session()
    try:
        q = session.query(PaperOrderModel)
        q = _apply_filters(q, PaperOrderModel, symbol, status, side, date_from, date_to)
        total = q.count()
        rows = q.order_by(PaperOrderModel.created_at.desc()).offset(offset).limit(limit).all()
        return {
            "orders": [_serialize_order(r) for r in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    finally:
        session.close()


@router.get("/paper/orders/{order_id}")
def get_order(order_id: int):
    session = get_session()
    try:
        order = session.query(PaperOrderModel).filter(PaperOrderModel.id == order_id).first()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return _serialize_order(order)
    finally:
        session.close()


# ── Trades (PaperTrade journal) ─────────────────────────────────────────────


@router.get("/paper/trades")
def list_trades(
    symbol: Optional[str] = Query(None, min_length=1, max_length=20),
    status: Optional[str] = Query(None, pattern="^(OPEN|TAKE_PROFIT|STOP_LOSS|CLOSED|CANCEL)$"),
    side: Optional[str] = Query(None, pattern="^(LONG|SHORT)$"),
    date_from: Optional[str] = Query(None, alias="date_from"),
    date_to: Optional[str] = Query(None, alias="date_to"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_session()
    try:
        q = session.query(PaperTradeModel)
        q = _apply_filters(q, PaperTradeModel, symbol, status, side, date_from, date_to)
        total = q.count()
        rows = q.order_by(PaperTradeModel.created_at.desc()).offset(offset).limit(limit).all()
        return {
            "trades": [_serialize_trade(r) for r in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    finally:
        session.close()


@router.get("/paper/trades/{trade_id}")
def get_trade(trade_id: int):
    session = get_session()
    try:
        t = session.query(PaperTradeModel).filter(PaperTradeModel.id == trade_id).first()
        if t is None:
            raise HTTPException(status_code=404, detail="Trade not found")
        return _serialize_trade(t)
    finally:
        session.close()


# ── Positions (Trade table) ──────────────────────────────────────────────────


@router.get("/paper/positions")
def list_positions(
    symbol: Optional[str] = Query(None, min_length=1, max_length=20),
    status: Optional[str] = Query(None, pattern="^(OPEN|TAKE_PROFIT|STOP_LOSS|CLOSED|CANCEL)$"),
    side: Optional[str] = Query(None, pattern="^(LONG|SHORT)$"),
    date_from: Optional[str] = Query(None, alias="date_from"),
    date_to: Optional[str] = Query(None, alias="date_to"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_session()
    try:
        q = session.query(Trade)
        q = _apply_filters(q, Trade, symbol, status, side, date_from, date_to)
        total = q.count()
        rows = q.order_by(Trade.created_at.desc()).offset(offset).limit(limit).all()
        return {
            "positions": [_serialize_position(r) for r in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    finally:
        session.close()


# ── Summary ──────────────────────────────────────────────────────────────────


@router.get("/paper/summary")
def get_paper_summary():
    session = get_session()
    try:
        total_orders = session.query(PaperOrderModel).count()
        pending_orders = session.query(PaperOrderModel).filter(PaperOrderModel.status == PENDING).count()
        filled_orders = session.query(PaperOrderModel).filter(PaperOrderModel.status == FILLED).count()
        cancelled_orders = session.query(PaperOrderModel).filter(PaperOrderModel.status == CANCEL).count()

        total_trades = session.query(PaperTradeModel).count()
        open_trades = session.query(PaperTradeModel).filter(PaperTradeModel.status == OPEN).count()
        closed_trades = session.query(PaperTradeModel).filter(
            PaperTradeModel.status.in_({TAKE_PROFIT, STOP_LOSS, CLOSED}),
        ).count()

        total_positions = session.query(Trade).count()
        open_positions = session.query(Trade).filter(Trade.status == OPEN).count()

        winning_trades = session.query(PaperTradeModel).filter(
            PaperTradeModel.pnl.isnot(None),
            PaperTradeModel.pnl > 0,
        ).count()
        losing_trades = session.query(PaperTradeModel).filter(
            PaperTradeModel.pnl.isnot(None),
            PaperTradeModel.pnl < 0,
        ).count()
        total_wl = winning_trades + losing_trades
        total_pnl = (
            session.query(PaperTradeModel)
            .filter(PaperTradeModel.pnl.isnot(None))
            .with_entities(PaperTradeModel.pnl)
            .all()
        )
        pnl_sum = sum(row[0] for row in total_pnl if row[0] is not None)

        return {
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "filled": filled_orders,
                "cancelled": cancelled_orders,
            },
            "trades": {
                "total": total_trades,
                "open": open_trades,
                "closed": closed_trades,
            },
            "positions": {
                "total": total_positions,
                "open": open_positions,
            },
            "performance": {
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(winning_trades / total_wl * 100, 2) if total_wl > 0 else 0.0,
                "total_pnl": round(pnl_sum, 2),
            },
        }
    finally:
        session.close()
