from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter

from database import Trade, get_session
from execution.paper_executor import PaperExecutor as PaperExec
from portfolio_engine import PortfolioEngine

router = APIRouter()

FINAL_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})


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
        all_trades = session.query(Trade).all()
    finally:
        session.close()

    open_trades = [t for t in all_trades if str(t.status) == "OPEN"]
    closed_trades = [t for t in all_trades if str(t.status) in FINAL_STATUSES]
    winning = [t for t in closed_trades if t.pnl is not None and t.pnl > 0]
    losing = [t for t in closed_trades if t.pnl is not None and t.pnl < 0]
    total_wl = len(winning) + len(losing)

    return {
        "open": [
            {
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "entry": t.entry,
                "stop": t.stop,
                "tp1": t.tp1,
                "tp2": t.tp2,
                "status": t.status,
                "pnl": t.pnl,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in open_trades
        ],
        "closed": [
            {
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "entry": t.entry,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "status": t.status,
                "close_reason": t.close_reason,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "closed_at": t.closed_at.isoformat() if t.closed_at else None,
            }
            for t in closed_trades
        ],
        "performance": {
            "total_trades": len(all_trades),
            "open_trades": len(open_trades),
            "closed_trades": len(closed_trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round((len(winning) / total_wl * 100), 2) if total_wl > 0 else 0.0,
            "total_pnl": round(sum(t.pnl for t in closed_trades if t.pnl is not None), 2),
        },
    }
