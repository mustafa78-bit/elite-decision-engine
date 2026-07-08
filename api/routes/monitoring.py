from fastapi import APIRouter

from database import Notification, Trade, Signal, get_session
from config import API_ENV, DEBUG
from monitoring.health import HealthService

router = APIRouter()


def _db_status() -> dict:
    try:
        session = get_session()
        session.execute(Notification.__table__.select().limit(1))
        session.close()
        return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/monitoring")
def get_monitoring():
    db = _db_status()
    exec_status = HealthService.execution()
    deps = HealthService.dependencies()
    errs = HealthService.errors()

    trade_counts = {"total": 0, "open": 0, "closed": 0}
    signal_count = 0
    notification_count = 0

    if db["status"] == "connected":
        session = get_session()
        try:
            all_trades = session.query(Trade).all()
            trade_counts["total"] = len(all_trades)
            trade_counts["open"] = len([t for t in all_trades if t.status == "OPEN"])
            trade_counts["closed"] = len([t for t in all_trades if t.status in {"TP_HIT", "SL_HIT", "CLOSED"}])
            signal_count = session.query(Signal).count()
            notification_count = session.query(Notification).count()
        finally:
            session.close()

    metrics = HealthService.metrics()

    return {
        "system": {
            "api_env": API_ENV,
            "debug": DEBUG,
        },
        "database": db,
        "execution": exec_status,
        "dependencies": deps,
        "errors": errs if errs else None,
        "metrics": metrics,
        "engines": {
            "trade_count": trade_counts,
            "signal_count": signal_count,
            "notification_count": notification_count,
        },
    }


@router.get("/health/details")
def health_details():
    return HealthService.full()
