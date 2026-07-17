import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional


@dataclass
class HealthStatus:
    status: str = "healthy"
    modules: Dict[str, bool] = field(default_factory=dict)
    database: str = "unknown"
    uptime_seconds: float = 0.0
    version: str = "1.0.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "modules": dict(self.modules), "database": self.database,
                "uptime_seconds": self.uptime_seconds, "version": self.version, "timestamp": self.timestamp}


@dataclass
class MetricsResponse:
    evaluate_calls: int = 0
    modules_active: int = 0
    decisions_made: int = 0
    signals_processed: int = 0
    uptime_seconds: float = 0.0
    memory_entries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"evaluate_calls": self.evaluate_calls, "modules_active": self.modules_active,
                "decisions_made": self.decisions_made, "signals_processed": self.signals_processed,
                "uptime_seconds": self.uptime_seconds, "memory_entries": self.memory_entries}


_SECRET_ENV_KEYS = [
    "POSTGRES_PASSWORD",
    "TELEGRAM_TOKEN",
    "HL_API_KEY",
    "HL_SECRET",
]


def check_secrets() -> List[str]:
    import os
    missing = []
    for key in _SECRET_ENV_KEYS:
        if not os.getenv(key):
            missing.append(key)
    return missing


def validate_startup_config() -> List[str]:
    import os
    import re
    warnings = []
    required = ["POSTGRES_HOST", "POSTGRES_DB"]
    for key in required:
        if not os.getenv(key):
            warnings.append(f"Required env {key} not set")
    port = os.getenv("POSTGRES_PORT", "5432")
    try:
        p = int(port)
        if not (0 < p <= 65535):
            warnings.append(f"POSTGRES_PORT={port} out of range")
    except ValueError:
        warnings.append(f"POSTGRES_PORT={port} not a valid integer")
    if os.getenv("TELEGRAM_TOKEN") and not re.match(r"^\d+:[A-Za-z0-9_-]+$", os.getenv("TELEGRAM_TOKEN", "")):
        warnings.append("TELEGRAM_TOKEN format looks invalid")
    return warnings


class HealthChecker:

    def __init__(self, engine=None):
        self._engine = engine
        self._start_time: Optional[float] = None
        self._lock = Lock()
        self._healthy = True
        self._db_healthy = "unknown"
        self._last_check_result: Optional[HealthStatus] = None
        self._module_history: Dict[str, List[bool]] = {}
        self._cache_stats_provider = None

    def set_cache_stats_provider(self, provider) -> None:
        self._cache_stats_provider = provider

    def start(self) -> None:
        self._start_time = time.time()

    def stop(self) -> None:
        pass

    def check(self) -> HealthStatus:
        modules = {}
        db_status = "unknown"
        if self._engine and self._engine.intelligence:
            try:
                result = self._engine.intelligence.evaluate()
                for mod in ("whale", "liquidity", "orderflow", "market_structure", "news", "sentiment", "macro"):
                    mod_data = result.get(mod, {})
                    ok = mod_data.get("ok", False)
                    modules[mod] = ok
                    if mod not in self._module_history:
                        self._module_history[mod] = []
                    self._module_history[mod].append(ok)
                    if len(self._module_history[mod]) > 100:
                        self._module_history[mod] = self._module_history[mod][-100:]
                db_status = "connected" if result.get("btc", {}).get("ok", False) else "degraded"
            except Exception:
                modules = {m: False for m in ("whale", "liquidity", "orderflow", "market_structure", "news", "sentiment", "macro")}
                db_status = "error"

        with self._lock:
            self._db_healthy = db_status

        uptime = 0.0
        if self._start_time is not None:
            uptime = time.time() - self._start_time

        overall = "healthy"
        if any(not v for v in modules.values()):
            overall = "degraded"
        if db_status == "error":
            overall = "unhealthy"

        result = HealthStatus(
            status=overall,
            modules=modules,
            database=db_status,
            uptime_seconds=round(uptime, 2),
            version="1.0.0",
        )
        self._last_check_result = result
        return result

    def is_ready(self) -> bool:
        try:
            status = self.check()
            return status.status != "unhealthy"
        except Exception:
            return False

    def is_alive(self) -> bool:
        return self._healthy

    def get_metrics(self) -> MetricsResponse:
        evaluate_calls = 0
        modules_active = 0
        decisions_made = 0
        memory_entries = 0

        if self._engine:
            if hasattr(self._engine.intelligence, "monitoring"):
                evaluate_calls = self._engine.intelligence.monitoring.get("evaluate_calls", 0)
                modules_active = self._engine.intelligence.monitoring.get("modules_active", 0)
            decisions_made = len(getattr(self._engine, "decision_history", []))

        uptime = 0.0
        if self._start_time is not None:
            uptime = time.time() - self._start_time

        return MetricsResponse(
            evaluate_calls=evaluate_calls,
            modules_active=modules_active,
            decisions_made=decisions_made,
            signals_processed=decisions_made,
            uptime_seconds=round(uptime, 2),
            memory_entries=memory_entries,
        )

    def get_extended_metrics(self) -> Dict[str, Any]:
        metrics = self.get_metrics()
        result = metrics.to_dict()
        result["database_status"] = self._db_healthy
        secret_warnings = check_secrets()
        config_warnings = validate_startup_config()
        result["secret_warnings_count"] = len(secret_warnings)
        result["config_warnings_count"] = len(config_warnings)
        if self._cache_stats_provider:
            try:
                provider = self._cache_stats_provider
                if hasattr(provider, "get_stats"):
                    result["cache"] = provider.get_stats()
                elif callable(provider):
                    result["cache"] = provider()
                else:
                    result["cache"] = {"size": 0}
            except Exception:
                result["cache"] = {"size": 0}
        result["module_history"] = {
            mod: {"healthy": sum(1 for v in vals if v), "total": len(vals), "stability": round(sum(1 for v in vals if v) / len(vals), 2) if vals else 0}
            for mod, vals in self._module_history.items()
        }
        return result

    def get_db_status(self) -> str:
        return self._db_healthy
