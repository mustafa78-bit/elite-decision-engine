"""Prometheus text-exposition metrics for GET /metrics.

Reuses monitoring.health.HealthService's already-computed data rather than
running its own separate checks -- the JSON /health/details endpoint and
this one are two views of the same underlying health state, not two
independent sources of truth.
"""

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest

from monitoring.health import HealthService

REGISTRY = CollectorRegistry()

UPTIME_SECONDS = Gauge(
    "elite_uptime_seconds", "Process uptime in seconds", registry=REGISTRY,
)
COMPONENT_HEALTHY = Gauge(
    "elite_component_healthy", "1 if the component's last check was ok, 0 otherwise",
    ["component"], registry=REGISTRY,
)
COMPONENT_LATENCY_MS = Gauge(
    "elite_component_latency_ms", "Latency of the component's last health check, in milliseconds",
    ["component"], registry=REGISTRY,
)
COMPONENT_CONSECUTIVE_ERRORS = Gauge(
    "elite_component_consecutive_errors", "Consecutive health-check failures for a component",
    ["component"], registry=REGISTRY,
)
SIGNALS_TOTAL = Gauge(
    "elite_signals_total", "Signal row count by status", ["status"], registry=REGISTRY,
)
TRADES_TOTAL = Gauge(
    "elite_trades_total", "Trade row count by status", ["status"], registry=REGISTRY,
)

# Health checks that report a "latency_ms" field -- matches
# HealthService.full()'s own component set, kept explicit here rather than
# introspected so a future new check must be a deliberate addition to this
# file, not an automatic (and possibly wrong) inclusion.
_LATENCY_COMPONENTS = ("database", "database_tables", "collector", "execution")


def collect_metrics() -> bytes:
    """Snapshot current values from HealthService into the module-level
    gauges and serialize them in the Prometheus text exposition format.
    """
    full = HealthService.full()

    UPTIME_SECONDS.set(full["uptime_seconds"])

    component_checks = {
        "database": full["database"],
        "database_tables": full["database_tables"],
        "collector": full["collector"],
        "execution": full["execution"],
        "cache": full["cache"],
        "metrics": full["metrics"],
        **full["dependencies"],
    }
    for component, result in component_checks.items():
        COMPONENT_HEALTHY.labels(component=component).set(1 if result.get("status") == "ok" else 0)
        if component in _LATENCY_COMPONENTS and "latency_ms" in result:
            COMPONENT_LATENCY_MS.labels(component=component).set(result["latency_ms"])

    for component, err in full["errors"].items():
        COMPONENT_CONSECUTIVE_ERRORS.labels(component=component).set(err["consecutive_failures"])

    signals = full["metrics"].get("signals", {})
    for status, count in signals.items():
        SIGNALS_TOTAL.labels(status=status).set(count)

    trades = full["metrics"].get("trades", {})
    for status, count in trades.items():
        TRADES_TOTAL.labels(status=status).set(count)

    return generate_latest(REGISTRY)


__all__ = ["CONTENT_TYPE_LATEST", "collect_metrics"]
