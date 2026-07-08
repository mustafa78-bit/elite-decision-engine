from fastapi import APIRouter

from database import Signal, Trade, get_session
from notifications.dispatcher import NotificationDispatcher

router = APIRouter()

FINAL_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})


@router.get("/execution/status")
def get_execution_status():
    session = get_session()
    try:
        all_signals = session.query(Signal).all()
        all_trades = session.query(Trade).all()
    finally:
        session.close()

    total_signals = len(all_signals)
    approved_signals = len([s for s in all_signals if str(s.status) in {"EXECUTED", "OPEN"}])
    rejected_signals = len([s for s in all_signals if str(s.status) == "REJECTED"])
    pending_signals = len([s for s in all_signals if str(s.status) == "OPEN"])

    open_trades = [t for t in all_trades if str(t.status) == "OPEN"]
    closed_trades = [t for t in all_trades if str(t.status) in FINAL_STATUSES]
    tp_hit = len([t for t in closed_trades if str(t.status) == "TP_HIT"])
    sl_hit = len([t for t in closed_trades if str(t.status) == "SL_HIT"])

    return {
        "signals": {
            "total": total_signals,
            "approved": approved_signals,
            "rejected": rejected_signals,
            "pending": pending_signals,
            "execution_rate": round((approved_signals / total_signals * 100), 2) if total_signals > 0 else 0.0,
        },
        "trades": {
            "total": len(all_trades),
            "open": len(open_trades),
            "closed": len(closed_trades),
            "tp_hit": tp_hit,
            "sl_hit": sl_hit,
        },
        "errors": [],
    }
