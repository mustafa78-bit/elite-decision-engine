from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter

from database import FINAL_STATUSES, PaperTrade, Trade, get_session
from execution.paper_executor import PaperExecutor as PaperExec
from portfolio_engine import PortfolioEngine

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


@dataclass
class PaperPerformance:
    total_trades: int = 0
    open_trades: int = 0
    closed_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0


@router.get("/paper-trading")
def get_paper_trading():
    session = get_session()
    try:
        results = session.query(Trade, PaperTrade).outerjoin(
            PaperTrade, PaperTrade.position_id == Trade.id
        ).all()
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

        # Calculate real dollar pnl
        if t.pnl is None:
            real_pnl = None
        elif pt is not None:
            real_pnl = (pt.quantity or 0.0) * t.pnl
        else:
            real_pnl = t.pnl

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
