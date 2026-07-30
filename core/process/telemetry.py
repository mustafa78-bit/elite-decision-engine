# core/process/telemetry.py
"""Process Scheduler observability metrics and manifest drift detection."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class SchedulerMetrics:
    """Consolidated metrics reflecting process scheduler execution and guarantees."""

    processes_queued: int = 0
    processes_completed: int = 0
    processes_failed: int = 0
    yields_triggered: int = 0
    interrupts_processed: int = 0
    guarantee_violations: int = 0  # Scheduling Guarantee Violations count
    drift_incidents: int = 0  # Manifest Drift Detection incidents
    retry_attempts: int = 0


class TelemetryService:
    """Manages scheduler telemetry tracking and manifest drift detection logs."""

    def __init__(self) -> None:
        self.metrics = SchedulerMetrics()
        self._drift_log: List[Dict[str, Any]] = []

    def record_completed(self) -> None:
        self.metrics.processes_completed += 1

    def record_failed(self) -> None:
        self.metrics.processes_failed += 1

    def record_yield(self) -> None:
        self.metrics.yields_triggered += 1

    def record_interrupt(self) -> None:
        self.metrics.interrupts_processed += 1

    def record_guarantee_violation(self, process_id: str, message: str) -> None:
        """Increment guarantee violations metric (e.g. deadline or atomic limit breaches)."""
        self.metrics.guarantee_violations += 1
        logger.warning("[TELEMETRY] Scheduling Guarantee Violation: Process %s - %s", process_id, message)

    def detect_and_log_drift(
        self,
        process_id: str,
        allocated_cpu: float,
        actual_usage_cpu: float,
        threshold: float = 0.5,
    ) -> bool:
        """Detect drift between resource manifest requirements and actual execution metrics."""
        drift = abs(actual_usage_cpu - allocated_cpu)
        if drift > threshold:
            self.metrics.drift_incidents += 1
            incident = {
                "process_id": process_id,
                "allocated": allocated_cpu,
                "actual": actual_usage_cpu,
                "drift": drift,
            }
            self._drift_log.append(incident)
            logger.warning(
                "[TELEMETRY] Resource Manifest Drift Detected for %s: Allocated %s, Actual %s (Drift %s)",
                process_id, allocated_cpu, actual_usage_cpu, drift,
            )
            return True
        return False

    def get_drift_incidents(self) -> List[Dict[str, Any]]:
        return list(self._drift_log)

    def get_snapshot(self) -> Dict[str, int]:
        """Return raw performance and tracking metrics snapshot."""
        return {
            "processes_queued": self.metrics.processes_queued,
            "processes_completed": self.metrics.processes_completed,
            "processes_failed": self.metrics.processes_failed,
            "yields_triggered": self.metrics.yields_triggered,
            "interrupts_processed": self.metrics.interrupts_processed,
            "guarantee_violations": self.metrics.guarantee_violations,
            "drift_incidents": self.metrics.drift_incidents,
            "retry_attempts": self.metrics.retry_attempts,
        }
