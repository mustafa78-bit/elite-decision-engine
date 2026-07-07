from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.dependencies import get_current_user, require_admin, require_read
from api.routes.release import router as release_router
from api.websocket.manager import ConnectionManager
from release.readiness import ReadinessService
from release.shutdown import GracefulShutdown
from release.startup import StartupValidator
from release.version import VERSION, VersionService


class TestStartupValidator:

    def test_config_passes(self) -> None:
        validator = StartupValidator()
        result = validator.validate()
        assert result["config"]["ok"] is True

    def test_database_no_factory_fails(self) -> None:
        validator = StartupValidator()
        result = validator.validate()
        assert result["database"]["ok"] is False
        assert "No session_factory" in result["database"]["error"]

    def test_api_always_passes(self) -> None:
        validator = StartupValidator()
        result = validator.validate()
        assert result["api"]["ok"] is True

    def test_websocket_no_manager_fails(self) -> None:
        validator = StartupValidator()
        result = validator.validate()
        assert result["websocket"]["ok"] is False
        assert "WebSocket manager not configured" in result["websocket"]["error"]

    def test_monitoring_no_service_fails(self) -> None:
        validator = StartupValidator()
        result = validator.validate()
        assert result["monitoring"]["ok"] is False
        assert "Monitoring service not configured" in result["monitoring"]["error"]

    def test_all_pass_false_on_failures(self) -> None:
        validator = StartupValidator()
        result = validator.validate()
        assert result["all_pass"] is False

    def test_all_pass_true_when_configured(self) -> None:
        mock_session = MagicMock()
        mock_execute = MagicMock()
        mock_session.execute.return_value = True
        session_factory = MagicMock(return_value=mock_session)

        validator = StartupValidator(
            session_factory=session_factory,
            ws_manager=MagicMock(),
            monitoring_service=MagicMock(),
        )
        result = validator.validate()
        assert result["all_pass"] is True
        for key in ("config", "database", "api", "websocket", "monitoring"):
            assert result[key]["ok"] is True, f"{key} should be ok"


class TestGracefulShutdown:

    def test_shutdown_returns_all_keys(self) -> None:
        ws = MagicMock()
        ws.active_count = 2
        shutdown = GracefulShutdown(ws_manager=ws)
        result = shutdown.shutdown()
        assert "database" in result
        assert "websocket_clients" in result
        assert "background_tasks" in result

    def test_database_closed(self) -> None:
        shutdown = GracefulShutdown()
        result = shutdown.shutdown()
        assert result["database"] == "closed"

    def test_websocket_disconnect_called(self) -> None:
        ws = MagicMock()
        ws.active_count = 3
        shutdown = GracefulShutdown(ws_manager=ws)
        result = shutdown.shutdown()
        assert result["websocket_clients"] == "disconnected_3"
        ws.disconnect_all.assert_called_once()

    def test_websocket_no_manager(self) -> None:
        shutdown = GracefulShutdown()
        result = shutdown.shutdown()
        assert result["websocket_clients"] == "no_manager"

    def test_background_tasks_noop(self) -> None:
        shutdown = GracefulShutdown()
        result = shutdown.shutdown()
        assert result["background_tasks"] == "noop"


class TestReadinessService:

    def test_is_ready_no_validator(self) -> None:
        svc = ReadinessService()
        assert svc.is_ready() == {"ready": True}

    def test_is_ready_validator_passes(self) -> None:
        validator = MagicMock()
        validator.validate.return_value = {"all_pass": True}
        svc = ReadinessService(startup_validator=validator)
        assert svc.is_ready() == {"ready": True}

    def test_is_ready_validator_fails(self) -> None:
        validator = MagicMock()
        validator.validate.return_value = {"all_pass": False}
        svc = ReadinessService(startup_validator=validator)
        assert svc.is_ready() == {"ready": False}


class TestVersionService:

    def test_get_version_contains_keys(self) -> None:
        svc = VersionService()
        result = svc.get_version()
        assert "version" in result
        assert "python" in result
        assert "platform" in result
        assert "commit" in result

    def test_version_string(self) -> None:
        svc = VersionService()
        result = svc.get_version()
        assert result["version"] == VERSION

    def test_python_version_string(self) -> None:
        svc = VersionService()
        result = svc.get_version()
        assert len(result["python"]) > 0


class TestReleaseEndpoints:

    @pytest.fixture
    def app(self) -> FastAPI:
        _app = FastAPI()
        _app.state.readiness_service = MagicMock()
        _app.state.readiness_service.is_ready.return_value = {"ready": True}
        _app.state.version_service = MagicMock()
        _app.state.version_service.get_version.return_value = {
            "version": "1.0.0",
            "python": "3.13",
            "platform": "linux",
            "commit": "abc1234",
        }
        _app.include_router(release_router)

        async def _mock_user() -> dict[str, Any]:
            return {"sub": "admin", "role": "ADMIN"}

        _app.dependency_overrides[get_current_user] = _mock_user
        _app.dependency_overrides[require_admin] = _mock_user
        _app.dependency_overrides[require_read] = _mock_user
        return _app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        return TestClient(app)

    def test_ready_endpoint(self, client: TestClient) -> None:
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"ready": True}

    def test_version_endpoint(self, client: TestClient) -> None:
        resp = client.get("/version")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"
        assert data["python"] == "3.13"
        assert data["platform"] == "linux"
        assert data["commit"] == "abc1234"

    def test_no_auth_returns_401(self, app: FastAPI) -> None:
        app.dependency_overrides.clear()
        client = TestClient(app)
        for path in ("/ready", "/version"):
            resp = client.get(path)
            assert resp.status_code == 401, f"{path} returned {resp.status_code}"

    def test_viewer_can_access(self, app: FastAPI) -> None:
        async def _viewer() -> dict[str, Any]:
            return {"sub": "viewer", "role": "VIEWER"}

        app.dependency_overrides[get_current_user] = _viewer
        app.dependency_overrides[require_read] = _viewer
        client = TestClient(app)

        for path in ("/ready", "/version"):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"


class TestConnectionManagerDisconnectAll:

    def test_disconnect_all_removes_all(self) -> None:
        mgr = ConnectionManager()
        mgr._connections = {"a": MagicMock(), "b": MagicMock(), "c": MagicMock()}
        assert mgr.active_count == 3
        mgr.disconnect_all()
        assert mgr.active_count == 0

    def test_disconnect_all_empty(self) -> None:
        mgr = ConnectionManager()
        mgr.disconnect_all()
        assert mgr.active_count == 0
