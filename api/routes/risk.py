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
from database import FINAL_STATUSES, Trade, get_session
from position_sizing import PositionSizingEngine
from risk.models import RejectionCode
from risk_manager import RiskManager
from scoring.risk_engine import RiskEngine
from services.pnl import query_trades_with_dollar_pnl, query_trades_with_exposure

router = APIRouter()


@router.get("/risk")
def get_risk():
    session = get_session()
    try:
        trades_with_pnl = query_trades_with_dollar_pnl(session)
        open_trades_with_exposure = query_trades_with_exposure(session, Trade.status == "OPEN")
    finally:
        session.close()

    open_count = len(open_trades_with_exposure)
    symbol_exposure: dict[str, float] = {}
    for t, exposure in open_trades_with_exposure:
        sym = t.symbol or "?"
        symbol_exposure[sym] = symbol_exposure.get(sym, 0) + exposure

    portfolio_exposure = sum(exposure for t, exposure in open_trades_with_exposure)

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    def is_today(closed_at):
        if closed_at is None:
            return False
        ca = closed_at.replace(tzinfo=None) if closed_at.tzinfo else closed_at
        ts = today_start.replace(tzinfo=None)
        return ca >= ts

    daily_loss = sum(
        pnl_val
        for t, pnl_val in trades_with_pnl
        if t.status in FINAL_STATUSES
        and pnl_val < 0
        and is_today(t.closed_at)
    )

    risk_engine = RiskEngine()
    risk_assessment = risk_engine.evaluate({"atr": 0}, {"score": 0})

    return {
        "risk_score": risk_assessment["risk_score"],
        "risk_penalties": risk_assessment["penalties"],
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


@router.get("/risk/limits")
def get_risk_limits():
    return {
        "max_open_trades": MAX_OPEN_TRADES,
        "max_exposure_per_symbol": MAX_EXPOSURE_PER_SYMBOL,
        "max_portfolio_exposure": MAX_PORTFOLIO_EXPOSURE,
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
