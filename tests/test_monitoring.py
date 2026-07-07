from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.dependencies import get_current_user, require_admin, require_read
from api.routes.monitoring import router as monitoring_router
from core.health_check import HealthReport, HealthStatus
from core.kill_switch import KillSwitch
from monitoring.diagnostics import DiagnosticsService
from monitoring.health import HealthService
from monitoring.metrics import MetricsService
from monitoring.service import MonitoringService


@pytest.fixture
def mock_ws_manager() -> MagicMock:
    m = MagicMock()
    m.active_count = 3
    return m


@pytest.fixture
def mock_session() -> MagicMock:
    session = MagicMock()
    query = MagicMock()
    query.filter.return_value.count.return_value = 5
    session.query.return_value = query
    return session


@pytest.fixture
def metrics_service(mock_ws_manager: MagicMock, mock_session: MagicMock) -> MetricsService:
    ks = KillSwitch()
    return MetricsService(
        kill_switch=ks,
        ws_manager=mock_ws_manager,
        session_factory=MagicMock(return_value=mock_session),
    )


@pytest.fixture
def health_service() -> HealthService:
    hc = MagicMock()
    hc.run.return_value = HealthReport(
        overall_status=HealthStatus.HEALTHY,
        checks={"database": HealthStatus.HEALTHY, "logging": HealthStatus.HEALTHY},
        duration_ms=5.0,
    )
    return HealthService(health_check=hc)


@pytest.fixture
def diagnostics_service(mock_session: MagicMock) -> DiagnosticsService:
    session = MagicMock()
    execute = MagicMock()
    session.execute.return_value = True
    session_factory = MagicMock(return_value=session)
    return DiagnosticsService(session_factory=session_factory)


@pytest.fixture
def app(
    metrics_service: MetricsService,
    health_service: HealthService,
    diagnostics_service: DiagnosticsService,
    mock_ws_manager: MagicMock,
) -> FastAPI:
    _app = FastAPI()
    _app.state.kill_switch = KillSwitch()
    _app.state.ws_manager = mock_ws_manager
    _app.state.health_check = MagicMock()
    _app.state.session_factory = MagicMock()

    from database import get_session
    _app.state.monitoring_service = MonitoringService(
        kill_switch=_app.state.kill_switch,
        health_check=_app.state.health_check,
        ws_manager=_app.state.ws_manager,
        session_factory=get_session,
    )
    _app.state.monitoring_service._metrics = metrics_service
    _app.state.monitoring_service._health = health_service
    _app.state.monitoring_service._diagnostics = diagnostics_service

    _app.include_router(monitoring_router)

    async def _mock_user() -> dict[str, Any]:
        return {"sub": "admin", "role": "ADMIN"}

    _app.dependency_overrides[get_current_user] = _mock_user
    _app.dependency_overrides[require_admin] = _mock_user
    _app.dependency_overrides[require_read] = _mock_user
    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestMetricsService:

    def test_snapshot_contains_all_keys(self, metrics_service: MetricsService) -> None:
        snap = metrics_service.snapshot()
        assert "uptime_seconds" in snap
        assert "request_count" in snap
        assert "active_ws_clients" in snap
        assert "open_trades" in snap
        assert "engine_state" in snap

    def test_request_count_increments(self, metrics_service: MetricsService) -> None:
        assert metrics_service.request_count == 0
        metrics_service.increment_requests()
        assert metrics_service.request_count == 1
        metrics_service.increment_requests()
        assert metrics_service.request_count == 2

    def test_uptime_positive(self, metrics_service: MetricsService) -> None:
        assert metrics_service.uptime_seconds >= 0

    def test_ws_clients_from_manager(self, metrics_service: MetricsService) -> None:
        snap = metrics_service.snapshot()
        assert snap["active_ws_clients"] == 3

    def test_open_trades_from_db(self, metrics_service: MetricsService) -> None:
        snap = metrics_service.snapshot()
        assert snap["open_trades"] == 5

    def test_engine_state_running(self, metrics_service: MetricsService) -> None:
        snap = metrics_service.snapshot()
        assert snap["engine_state"] == "RUNNING"


class TestHealthService:

    def test_summary_contains_all_keys(self, health_service: HealthService) -> None:
        result = health_service.summary()
        assert "overall" in result
        assert "checks" in result
        assert "warnings" in result
        assert "errors" in result
        assert "duration_ms" in result

    def test_summary_healthy(self, health_service: HealthService) -> None:
        result = health_service.summary()
        assert result["overall"] == "HEALTHY"
        assert result["checks"]["database"] == "HEALTHY"

    def test_summary_failed(self) -> None:
        hc = MagicMock()
        hc.run.return_value = HealthReport(
            overall_status=HealthStatus.FAILED,
            checks={"database": HealthStatus.FAILED},
            errors=["DB connection failed"],
            duration_ms=3.0,
        )
        svc = HealthService(health_check=hc)
        result = svc.summary()
        assert result["overall"] == "FAILED"
        assert result["errors"] == ["DB connection failed"]


class TestDiagnosticsService:

    def test_runtime_summary_contains_all_keys(self, diagnostics_service: DiagnosticsService) -> None:
        result = diagnostics_service.runtime_summary()
        assert "python_version" in result
        assert "platform" in result
        assert "database_connected" in result
        assert "api_status" in result

    def test_runtime_summary_has_python_version(self, diagnostics_service: DiagnosticsService) -> None:
        result = diagnostics_service.runtime_summary()
        assert len(result["python_version"]) > 0

    def test_runtime_summary_db_connected(self, diagnostics_service: DiagnosticsService) -> None:
        result = diagnostics_service.runtime_summary()
        assert result["database_connected"] is True

    def test_runtime_summary_api_status(self, diagnostics_service: DiagnosticsService) -> None:
        result = diagnostics_service.runtime_summary()
        assert result["api_status"] == "running"


class TestMonitoringEndpoints:

    def test_monitoring_root(self, client: TestClient) -> None:
        resp = client.get("/monitoring")
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data
        assert "health" in data
        assert "diagnostics" in data

    def test_monitoring_health(self, client: TestClient) -> None:
        resp = client.get("/monitoring/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall" in data
        assert "checks" in data

    def test_monitoring_metrics(self, client: TestClient) -> None:
        resp = client.get("/monitoring/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "uptime_seconds" in data
        assert "request_count" in data
        assert "active_ws_clients" in data
        assert "open_trades" in data
        assert "engine_state" in data

    def test_monitoring_diagnostics(self, client: TestClient) -> None:
        resp = client.get("/monitoring/diagnostics")
        assert resp.status_code == 200
        data = resp.json()
        assert "python_version" in data
        assert "platform" in data
        assert "database_connected" in data
        assert "api_status" in data


class TestMonitoringAuth:

    def test_no_auth_returns_401(self, app: FastAPI) -> None:
        app.dependency_overrides.clear()
        client = TestClient(app)
        resp = client.get("/monitoring")
        assert resp.status_code == 401

    def test_viewer_can_access(self, app: FastAPI) -> None:
        async def _viewer() -> dict[str, Any]:
            return {"sub": "viewer", "role": "VIEWER"}

        app.dependency_overrides[get_current_user] = _viewer
        app.dependency_overrides[require_read] = _viewer
        client = TestClient(app)

        for path in (
            "/monitoring",
            "/monitoring/health",
            "/monitoring/metrics",
            "/monitoring/diagnostics",
        ):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"
