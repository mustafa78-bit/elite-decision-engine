from fastapi import APIRouter, Response

from config import API_ENV, DEBUG
from database import FINAL_STATUSES, Notification, Signal, Trade, get_session
from monitoring.health import HealthService
from monitoring.metrics import CONTENT_TYPE_LATEST, collect_metrics

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
            trade_counts["closed"] = len([t for t in all_trades if t.status in FINAL_STATUSES])
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


@router.get("/metrics")
def metrics():
    """Prometheus text-exposition format -- a scraper's target, not a
    browser/JSON API endpoint. Public (no auth), matching /health's
    existing precedent: a real Prometheus scraper has no JWT to send, and
    this is expected to be reachable only from an internal
    network/firewalled scrape target, not the public internet.
    """
    return Response(content=collect_metrics(), media_type=CONTENT_TYPE_LATEST)
