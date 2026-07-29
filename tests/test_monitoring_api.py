from __future__ import annotations

import pytest


def test_monitoring_engineering_endpoint(api_client, db_session):
    from database import TelemetryEvent

    # Seed some telemetry event
    db_session.add(TelemetryEvent(screen="morning_brief", action="opened", duration=12.5))
    db_session.flush()

    resp = api_client.get("/monitoring/engineering")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "api_health" in body
    assert "websocket_health" in body
    assert "background_jobs" in body
    assert "performance_metrics" in body
    assert "recent_telemetry" in body
    assert len(body["recent_telemetry"]) >= 1
    assert body["recent_telemetry"][0]["screen"] == "morning_brief"
