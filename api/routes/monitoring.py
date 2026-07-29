from fastapi import APIRouter

from database import FINAL_STATUSES, Notification, Trade, Signal, get_session
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


@router.get("/monitoring/engineering")
def get_monitoring_engineering():
    """Engineering-only dashboard showing deep system metrics, telemetry, and background tasks."""
    from monitoring.health import HealthService
    from database import TelemetryEvent, get_session
    import api.main as main_app

    # Gather websocket states
    ws_clients = 0
    ws_rooms = {}
    bg_task_count = 0
    try:
        manager = getattr(main_app, "manager", None)
        if manager:
            ws_clients = len(manager._clients)
            for room, clients in manager._rooms.items():
                ws_rooms[room] = len(clients)

        bg_tasks = getattr(main_app, "_background_tasks", None)
        if bg_tasks:
            bg_task_count = len([t for t in bg_tasks if not t.done()])
    except Exception:
        pass

    # Database connections & latency
    db_health = HealthService.database()
    col_health = HealthService.collector()
    errs = HealthService.errors()

    # Recent Telemetry Events
    session = get_session()
    recent_telemetry = []
    try:
        events = session.query(TelemetryEvent).order_by(TelemetryEvent.timestamp.desc()).limit(10).all()
        recent_telemetry = [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "screen": e.screen,
                "action": e.action,
                "duration": e.duration,
                "outcome": e.outcome,
            }
            for e in events
        ]
    except Exception:
        pass
    finally:
        session.close()

    return {
        "status": "ok",
        "api_health": {
            "status": "healthy" if db_health.get("status") == "ok" else "degraded",
            "uptime_seconds": round(HealthService.uptime(), 2),
            "environment": API_ENV,
            "debug": DEBUG,
        },
        "websocket_health": {
            "total_clients": ws_clients,
            "rooms": ws_rooms,
        },
        "background_jobs": {
            "active_tasks_count": bg_task_count,
        },
        "performance_metrics": {
            "database_latency_ms": db_health.get("latency_ms", 0),
            "collector_latency_ms": col_health.get("latency_ms", 0),
        },
        "errors": errs if errs else {},
        "recent_telemetry": recent_telemetry,
    }
