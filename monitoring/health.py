from __future__ import annotations

from typing import Any

from core.health_check import HealthCheck


class HealthService:

    def __init__(self, health_check: HealthCheck) -> None:
        self._health_check = health_check

    def summary(self) -> dict[str, Any]:
        report = self._health_check.run()
        return {
            "overall": report.overall_status.value,
            "checks": {k: v.value for k, v in report.checks.items()},
            "warnings": report.warnings,
            "errors": report.errors,
            "duration_ms": report.duration_ms,
        }
