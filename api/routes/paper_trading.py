from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import or_

from api.dependencies import require_user_id
from database import FINAL_STATUSES, PaperTrade, Trade, get_session
from execution.paper_executor import PaperExecutor as PaperExec
from services.pnl import trade_dollar_pnl

router = APIRouter()


@dataclass
class PaperTradeSummary:
    id: int
    symbol: str
    side: str
    entry: float
    status: str
    pnl: float | None
    exit_price: float | None
    close_reason: str | None
    created_at: str | None


@router.get("/paper-trading")
def get_paper_trading(request: Request):
    user_id = require_user_id(request)
    session = get_session()
    try:
        results = (
            session.query(Trade, PaperTrade)
            .outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
            .filter(or_(Trade.user_id == user_id, Trade.user_id.is_(None)))
            .all()
        )
    finally:
        session.close()

    open_list = []
    closed_list = []
    closed_pnl_sum = 0.0

    winning_count = 0
    losing_count = 0
    total_wl = 0

    for t, pt in results:
        status_str = str(t.status)

        # Calculate real dollar pnl. Excludes trades with no matching
        # PaperTrade (real quantity unknown) rather than treating the raw
        # per-unit pnl as a dollar amount -- mirrors risk_manager.py's/
        # paper_executor.py's established "exclude, don't guess" handling
        # of the identical condition. real_pnl stays None either way (no
        # data yet vs. quantity unknown are both "N/A" to the caller).
        real_pnl = None if t.pnl is None else trade_dollar_pnl(t, pt)

        if status_str == "OPEN":
            open_list.append({
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "entry": t.entry,
                "stop": t.stop,
                "tp1": t.tp1,
                "tp2": t.tp2,
                "status": t.status,
                "pnl": real_pnl,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })
        elif status_str in FINAL_STATUSES:
            closed_list.append({
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "entry": t.entry,
                "exit_price": t.exit_price,
                "pnl": real_pnl,
                "status": t.status,
                "close_reason": t.close_reason,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "closed_at": t.closed_at.isoformat() if t.closed_at else None,
            })
            if real_pnl is not None:
                closed_pnl_sum += real_pnl

            # sign-based check for winning/losing
            if t.pnl is not None:
                if t.pnl > 0:
                    winning_count += 1
                    total_wl += 1
                elif t.pnl < 0:
                    losing_count += 1
                    total_wl += 1

    return {
        "open": open_list,
        "closed": closed_list,
        "performance": {
            "total_trades": len(results),
            "open_trades": len(open_list),
            "closed_trades": len(closed_list),
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "win_rate": round((winning_count / total_wl * 100), 2) if total_wl > 0 else 0.0,
            "total_pnl": round(closed_pnl_sum, 2),
        },
    }
