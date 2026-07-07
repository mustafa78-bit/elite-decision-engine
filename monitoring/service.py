from __future__ import annotations

from typing import Any, Callable

from core.health_check import HealthCheck
from core.kill_switch import KillSwitch
from monitoring.diagnostics import DiagnosticsService
from monitoring.health import HealthService
from monitoring.metrics import MetricsService


class MonitoringService:

    def __init__(
        self,
        kill_switch: KillSwitch,
        health_check: HealthCheck,
        ws_manager: Any,
        session_factory: Callable[[], Any],
    ) -> None:
        self._metrics = MetricsService(
            kill_switch=kill_switch,
            ws_manager=ws_manager,
            session_factory=session_factory,
        )
        self._health = HealthService(health_check=health_check)
        self._diagnostics = DiagnosticsService(
            session_factory=session_factory,
        )
