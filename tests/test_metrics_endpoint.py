"""Tests for GET /metrics -- the Prometheus scrape target.

monitoring/metrics.py reuses monitoring.health.HealthService's already-
computed data rather than running independent checks, so these tests
mostly confirm the JSON -> Prometheus text-exposition mapping is correct,
not health-check logic itself (already covered by tests/test_health_alerts.py
and monitoring/health.py's own call sites).
"""

import pytest

from database import Signal, Trade
from monitoring.health import HealthService


@pytest.fixture(autouse=True)
def _stub_collector_health(monkeypatch):
    # HealthService.collector() makes a real network call (MultiProvider ->
    # Hyperliquid) -- stub it so these tests exercise the JSON->Prometheus
    # mapping, not live network access, matching this file's own established
    # tests/test_health_alerts.py mocking convention.
    monkeypatch.setattr(
        HealthService, "collector",
        staticmethod(lambda symbol="BTC", timeout=10: {"status": "ok", "latency_ms": 5.0, "rows": 1}),
    )


def test_metrics_returns_prometheus_text_format(api_client):
    resp = api_client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    body = resp.text
    assert "elite_uptime_seconds" in body
    assert "elite_component_healthy" in body


def test_metrics_is_public_without_authentication(api_client):
    if "Authorization" in api_client.headers:
        del api_client.headers["Authorization"]
    resp = api_client.get("/metrics")
    assert resp.status_code == 200


def test_metrics_reflects_real_signal_and_trade_counts(api_client, db_session):
    db_session.add_all([
        Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN"),
        Signal(symbol="ETHUSDT", side="SHORT", timeframe="1h", status="OPEN"),
        Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, status="OPEN"),
    ])
    db_session.commit()

    resp = api_client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text

    assert 'elite_signals_total{status="open"} 2.0' in body
    assert 'elite_trades_total{status="open"} 1.0' in body


def test_metrics_component_healthy_reflects_status(api_client):
    resp = api_client.get("/metrics")
    body = resp.text
    assert 'elite_component_healthy{component="database"} 1.0' in body
