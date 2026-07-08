import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from config import API_ENV, CHECK_INTERVAL, MIN_SCORE, MAX_OPEN_TRADES
from database import get_session

logger = logging.getLogger(__name__)

_ENGINE_START_TIME: float = time.time()

_INTERNAL_ERRORS: dict[str, int] = {}
_LAST_SUCCESS: dict[str, float] = {}


@dataclass
class HealthComponent:
    status: str
    detail: str = ""
    latency_ms: float = 0.0
    last_success_ago: Optional[float] = None


def _track_result(component: str, ok: bool, latency: float) -> None:
    if ok:
        _LAST_SUCCESS[component] = time.time()
        _INTERNAL_ERRORS[component] = 0
    else:
        _INTERNAL_ERRORS.setdefault(component, 0)
        _INTERNAL_ERRORS[component] += 1


class HealthService:

    @staticmethod
    def uptime() -> float:
        return time.time() - _ENGINE_START_TIME

    @staticmethod
    def database() -> dict:
        start = time.monotonic()
        try:
            session = get_session()
            session.execute(__import__("sqlalchemy").text("SELECT 1"))
            session.close()
            lat = (time.monotonic() - start) * 1000
            _track_result("database", True, lat)
            return {
                "status": "ok",
                "latency_ms": round(lat, 1),
            }
        except Exception as e:
            lat = (time.monotonic() - start) * 1000
            _track_result("database", False, lat)
            msg = str(e).replace("password=***", "password=****")
            logger.warning("Database health check failed after %.0fms: %s", lat, msg)
            return {
                "status": "error",
                "latency_ms": round(lat, 1),
                "detail": msg,
            }

    @staticmethod
    def database_tables() -> dict:
        from database import Notification, Signal, Trade
        start = time.monotonic()
        try:
            session = get_session()
            counts = {}
            for name, table in [("signals", Signal), ("trades", Trade), ("notifications", Notification)]:
                try:
                    counts[name] = session.query(table).count()
                except Exception:
                    counts[name] = -1
            session.close()
            lat = (time.monotonic() - start) * 1000
            return {
                "status": "ok" if all(c >= 0 for c in counts.values()) else "degraded",
                "latency_ms": round(lat, 1),
                "row_counts": counts,
            }
        except Exception as e:
            lat = (time.monotonic() - start) * 1000
            return {
                "status": "error",
                "latency_ms": round(lat, 1),
                "detail": str(e),
            }

    @staticmethod
    def collector(symbol: str = "BTC", timeout: int = 10) -> dict:
        from market_data.collector import HyperliquidCollector
        start = time.monotonic()
        try:
            collector = HyperliquidCollector(timeout=timeout)
            df = collector.get_ohlcv(symbol=symbol, timeframe="1h", limit=1)
            ok = df is not None and not df.empty
            lat = (time.monotonic() - start) * 1000
            _track_result("collector", ok, lat)
            return {
                "status": "ok" if ok else "empty",
                "latency_ms": round(lat, 1),
                "rows": len(df) if df is not None and not df.empty else 0,
            }
        except Exception as e:
            lat = (time.monotonic() - start) * 1000
            _track_result("collector", False, lat)
            logger.warning("Collector health check failed after %.0fms: %s", lat, e)
            return {
                "status": "error",
                "latency_ms": round(lat, 1),
                "detail": str(e),
            }

    @staticmethod
    def cache() -> dict:
        try:
            from market_data.live.engine import LiveMarketEngine
            engine = LiveMarketEngine()
            status = "ok"
            cache_ttl = getattr(engine, "cache_ttl", None)
            cache_size = len(getattr(engine, "_cache", {}))
            return {
                "status": status,
                "cache_size": cache_size,
                "cache_ttl": cache_ttl,
            }
        except Exception as e:
            return {
                "status": "error",
                "detail": str(e),
            }

    @staticmethod
    def execution() -> dict:
        try:
            from execution.execution_loop import ExecutionLoop
            loop = ExecutionLoop()
            return {
                "status": "ok",
                "pipeline_ready": loop.pipeline is not None,
                "trade_engine_ready": loop.trade_engine is not None,
                "risk_manager_ready": loop.risk_manager is not None,
                "paper_executor_ready": loop.paper_executor is not None,
            }
        except Exception as e:
            return {
                "status": "error",
                "detail": str(e),
            }

    @staticmethod
    def dependencies() -> dict:
        deps = {}
        try:
            from exchange.hyperliquid.connector import HyperliquidExchange
            deps["hyperliquid_exchange"] = {"status": "ok"}
        except Exception as e:
            deps["hyperliquid_exchange"] = {"status": "error", "detail": str(e)}
        try:
            from exchange.binance.connector import BinanceExchange
            deps["binance_exchange"] = {"status": "ok"}
        except Exception as e:
            deps["binance_exchange"] = {"status": "error", "detail": str(e)}
        try:
            from notifications.dispatcher import NotificationDispatcher
            deps["notification_dispatcher"] = {"status": "ok"}
        except Exception as e:
            deps["notification_dispatcher"] = {"status": "error", "detail": str(e)}
        return deps

    @staticmethod
    def config() -> dict:
        return {
            "api_env": API_ENV,
            "check_interval": CHECK_INTERVAL,
            "min_score": MIN_SCORE,
            "max_open_trades": MAX_OPEN_TRADES,
        }

    @staticmethod
    def errors() -> dict:
        return {
            component: {
                "consecutive_failures": count,
                "last_success_ago": round(time.time() - _LAST_SUCCESS[component], 1)
                if component in _LAST_SUCCESS else None,
            }
            for component, count in sorted(_INTERNAL_ERRORS.items())
            if count > 0
        }

    @staticmethod
    def metrics() -> dict:
        from database import Signal, Trade
        try:
            session = get_session()
            total_signals = session.query(Signal).count()
            approved = session.query(Signal).filter(Signal.status == "EXECUTED").count()
            rejected = session.query(Signal).filter(Signal.status == "REJECTED").count()
            open_signals = session.query(Signal).filter(Signal.status == "OPEN").count()
            total_trades = session.query(Trade).count()
            open_trades = session.query(Trade).filter(Trade.status == "OPEN").count()
            closed_trades = session.query(Trade).filter(Trade.status.in_({"TP_HIT", "SL_HIT", "CLOSED"})).count()
            session.close()
            return {
                "status": "ok",
                "signals": {
                    "total": total_signals,
                    "approved": approved,
                    "rejected": rejected,
                    "open": open_signals,
                },
                "trades": {
                    "total": total_trades,
                    "open": open_trades,
                    "closed": closed_trades,
                },
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @staticmethod
    def full() -> dict:
        db = HealthService.database()
        tbl = HealthService.database_tables()
        col = HealthService.collector()
        cache = HealthService.cache()
        exec_status = HealthService.execution()
        deps = HealthService.dependencies()
        errs = HealthService.errors()
        met = HealthService.metrics()

        component_statuses = [db, col, cache, exec_status]
        for d in deps.values():
            component_statuses.append(d)
        overall = "ok"
        for s in component_statuses:
            if s.get("status") == "error":
                overall = "degraded"
                break

        return {
            "status": overall,
            "uptime_seconds": round(HealthService.uptime(), 2),
            "environment": API_ENV,
            "database": db,
            "database_tables": tbl,
            "collector": col,
            "cache": cache,
            "execution": exec_status,
            "dependencies": deps,
            "errors": errs,
            "metrics": met,
            "config": HealthService.config(),
        }


def check_database() -> dict:
    return HealthService.database()


def get_system_health() -> dict:
    return HealthService.full()
