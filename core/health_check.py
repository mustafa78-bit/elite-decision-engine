from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import config as config_module
from core.kill_switch import KillSwitch
from execution.live_executor import LiveExecutor
from execution.paper_executor import PaperExecutor
from execution.router import ExecutionRouter, TradingMode


class HealthStatus(Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    FAILED = "FAILED"


@dataclass
class HealthReport:
    overall_status: HealthStatus
    checks: dict[str, HealthStatus] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def is_failed(self) -> bool:
        return self.overall_status == HealthStatus.FAILED


class HealthCheck:

    def __init__(
        self,
        session_factory: Optional[Callable[[], Any]] = None,
        kill_switch: Optional[KillSwitch] = None,
        execution_router: Optional[ExecutionRouter] = None,
        log_dir: str = "logs",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._session_factory = session_factory
        self._kill_switch = kill_switch
        self._execution_router = execution_router
        self._log_dir = log_dir
        self.logger = logger or logging.getLogger(__name__)

    def run(self) -> HealthReport:
        start = time.perf_counter()
        checks: dict[str, HealthStatus] = {}
        warnings: list[str] = []
        errors: list[str] = []

        db_status, db_w, db_e = self._check_database()
        checks["database"] = db_status
        warnings.extend(db_w)
        errors.extend(db_e)

        log_status, log_w, log_e = self._check_logging()
        checks["logging"] = log_status
        warnings.extend(log_w)
        errors.extend(log_e)

        cfg_status, cfg_w, cfg_e = self._check_config()
        checks["configuration"] = cfg_status
        warnings.extend(cfg_w)
        errors.extend(cfg_e)

        ks_status, ks_w, ks_e = self._check_kill_switch()
        checks["kill_switch"] = ks_status
        warnings.extend(ks_w)
        errors.extend(ks_e)

        router_status, router_w, router_e = self._check_execution_router()
        checks["execution_router"] = router_status
        warnings.extend(router_w)
        errors.extend(router_e)

        paper_status, paper_w, paper_e = self._check_paper_executor()
        checks["paper_executor"] = paper_status
        warnings.extend(paper_w)
        errors.extend(paper_e)

        live_status, live_w, live_e = self._check_live_executor()
        checks["live_executor"] = live_status
        warnings.extend(live_w)
        errors.extend(live_e)

        duration = (time.perf_counter() - start) * 1000

        if errors:
            overall = HealthStatus.FAILED
        elif warnings:
            overall = HealthStatus.WARNING
        else:
            overall = HealthStatus.HEALTHY

        return HealthReport(
            overall_status=overall,
            checks=checks,
            warnings=warnings,
            errors=errors,
            duration_ms=round(duration, 2),
        )

    def _check_database(self) -> tuple[HealthStatus, list[str], list[str]]:
        if self._session_factory is None:
            return (
                HealthStatus.WARNING,
                ["No session_factory configured; database check skipped"],
                [],
            )
        session = self._session_factory()
        try:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            return HealthStatus.HEALTHY, [], []
        except Exception as e:
            return HealthStatus.FAILED, [], [f"Database check failed: {e}"]
        finally:
            session.close()

    def _check_logging(self) -> tuple[HealthStatus, list[str], list[str]]:
        try:
            os.makedirs(self._log_dir, exist_ok=True)
            test_file = os.path.join(self._log_dir, ".health_check_write_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            return HealthStatus.HEALTHY, [], []
        except Exception as e:
            return HealthStatus.FAILED, [], [f"Logging check failed: {e}"]

    def _check_config(self) -> tuple[HealthStatus, list[str], list[str]]:
        mandatory = [
            "DRY_RUN",
            "MAX_OPEN_TRADES",
            "ACCOUNT_EQUITY",
            "CHECK_INTERVAL",
            "MIN_SCORE",
            "MAX_POSITION_SIZE_USD",
            "RISK_PER_TRADE_PERCENT",
            "ATR_MULTIPLIER",
            "MIN_POSITION_QUANTITY",
        ]
        missing = [key for key in mandatory if not hasattr(config_module, key)]
        if missing:
            return (
                HealthStatus.FAILED,
                [],
                [f"Missing config variables: {', '.join(missing)}"],
            )
        return HealthStatus.HEALTHY, [], []

    def _check_kill_switch(self) -> tuple[HealthStatus, list[str], list[str]]:
        if self._kill_switch is None:
            return HealthStatus.FAILED, [], ["KillSwitch not configured"]
        if not self._kill_switch.is_running():
            return (
                HealthStatus.FAILED,
                [],
                [f"KillSwitch state is {self._kill_switch.state().value}, expected RUNNING"],
            )
        return HealthStatus.HEALTHY, [], []

    def _check_execution_router(self) -> tuple[HealthStatus, list[str], list[str]]:
        if self._execution_router is None:
            return HealthStatus.FAILED, [], ["ExecutionRouter not configured"]
        try:
            mode = self._execution_router.mode
            if mode not in (TradingMode.PAPER, TradingMode.LIVE):
                return (
                    HealthStatus.WARNING,
                    [f"ExecutionRouter mode is {mode.value}"],
                    [],
                )
            return HealthStatus.HEALTHY, [], []
        except Exception as e:
            return HealthStatus.FAILED, [], [f"ExecutionRouter check failed: {e}"]

    def _check_paper_executor(self) -> tuple[HealthStatus, list[str], list[str]]:
        try:
            PaperExecutor()
            return HealthStatus.HEALTHY, [], []
        except Exception as e:
            return HealthStatus.FAILED, [], [f"PaperExecutor instantiation failed: {e}"]

    def _check_live_executor(self) -> tuple[HealthStatus, list[str], list[str]]:
        try:
            LiveExecutor()
            return HealthStatus.HEALTHY, [], []
        except Exception as e:
            return HealthStatus.FAILED, [], [f"LiveExecutor instantiation failed: {e}"]
