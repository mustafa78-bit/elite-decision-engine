from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

from config import (
    MAX_DAILY_LOSS,
    MAX_EXPOSURE_PER_SYMBOL,
    MAX_OPEN_TRADES,
    MAX_POSITION_SIZE_USD,
    MAX_PORTFOLIO_EXPOSURE,
    ACCOUNT_EQUITY,
    RISK_PER_TRADE_PERCENT,
)
from database import Trade, get_session
from position_sizing import PositionSizingEngine
from scoring.risk_engine import RiskEngine

FINAL_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})

router = APIRouter()


@router.get("/risk")
def get_risk():
    session = get_session()
    try:
        all_trades = session.query(Trade).all()
    finally:
        session.close()

    open_trades = [t for t in all_trades if t.status == "OPEN"]
    closed_trades = [t for t in all_trades if t.status in FINAL_STATUSES]

    open_count = len(open_trades)
    symbol_exposure: dict[str, float] = {}
    for t in open_trades:
        sym = t.symbol or "?"
        symbol_exposure[sym] = symbol_exposure.get(sym, 0) + (t.entry or 0)

    portfolio_exposure = sum(t.entry or 0 for t in open_trades)

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    daily_loss = sum(
        t.pnl or 0
        for t in closed_trades
        if t.pnl is not None and t.pnl < 0
        and t.closed_at is not None
        and t.closed_at >= today_start
    )

    risk_engine = RiskEngine()
    risk_score = risk_engine.score({"atr": 0}, {"score": 0})

    return {
        "risk_score": risk_score,
        "open_trades": open_count,
        "max_open_trades": MAX_OPEN_TRADES,
        "symbol_exposure": symbol_exposure,
        "max_symbol_exposure": MAX_EXPOSURE_PER_SYMBOL,
        "portfolio_exposure": round(portfolio_exposure, 2),
        "max_portfolio_exposure": MAX_PORTFOLIO_EXPOSURE,
        "daily_loss": round(daily_loss, 2),
        "max_daily_loss": MAX_DAILY_LOSS,
        "max_position_size_usd": MAX_POSITION_SIZE_USD,
        "account_equity": ACCOUNT_EQUITY,
        "risk_per_trade_percent": RISK_PER_TRADE_PERCENT,
    }


@router.get("/position-sizing")
def get_position_sizing(
    entry: float = Query(...),
    atr: float = Query(0.0),
):
    class Candidate:
        def __init__(self, e, a):
            self.entry = e
            self.scores = {"atr": a}

    sizing = PositionSizingEngine()
    result = sizing.calculate(Candidate(entry, atr))
    return {
        "quantity": result.quantity,
        "notional_value": result.notional_value,
        "risk_amount": result.risk_amount,
    }
