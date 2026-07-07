from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.routes.auth import router as auth_router
from api.routes.control import router as control_router
from api.routes.health import router as health_router
from api.routes.performance import router as performance_router
from api.routes.portfolio import router as portfolio_router
from api.routes.trades import router as trades_router
from auth.jwt import SECRET_KEY, ALGORITHM, create_access_token
from auth.service import AuthService
from core.health_check import HealthReport, HealthStatus
from core.kill_switch import KillSwitch


@pytest.fixture
def auth_app() -> FastAPI:
    _app = FastAPI()
    _app.state.kill_switch = KillSwitch()
    _app.state.health_check = MagicMock()
    _app.state.portfolio_engine = MagicMock()
    _app.state.performance_engine = MagicMock()
    _app.state.session_factory = MagicMock()
    _app.state.dry_run = True
    _app.state.trading_mode = "PAPER"
    _app.state.auth_service = AuthService()
    _app.state.ws_manager = MagicMock()

    mock_report = HealthReport(
        overall_status=HealthStatus.HEALTHY,
        checks={"database": HealthStatus.HEALTHY},
        duration_ms=5.0,
    )
    _app.state.health_check.run.return_value = mock_report
    _app.state.portfolio_engine.stats.return_value = MagicMock(
        total_trades=0, open_trades=0, closed_trades=0,
        winning_trades=0, losing_trades=0, win_rate=0.0,
        total_pnl=0.0, daily_pnl=0.0, average_win=0.0,
        average_loss=0.0, profit_factor=0.0, max_drawdown=0.0,
        current_open_exposure=0.0,
    )
    _app.state.performance_engine.stats.return_value = MagicMock(
        sharpe_ratio=0.0, sortino_ratio=0.0, profit_factor=0.0,
        expectancy=0.0, recovery_factor=0.0, calmar_ratio=0.0,
        average_r_multiple=0.0, average_holding_hours=0.0,
        consecutive_wins=0, consecutive_losses=0,
        best_trade=0.0, worst_trade=0.0,
    )

    _app.include_router(auth_router)
    _app.include_router(health_router)
    _app.include_router(portfolio_router)
    _app.include_router(trades_router)
    _app.include_router(performance_router)
    _app.include_router(control_router)
    return _app


@pytest.fixture
def client(auth_app: FastAPI) -> TestClient:
    return TestClient(auth_app)


def _login(client: TestClient, username: str = "admin", password: str = "admin") -> dict:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()


class TestLogin:
    def test_login_success(self, client: TestClient) -> None:
        data = _login(client, "admin", "admin")
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_rejected(self, client: TestClient) -> None:
        resp = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_unknown_user_rejected(self, client: TestClient) -> None:
        resp = client.post("/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    def test_login_all_roles(self, client: TestClient) -> None:
        for username in ("admin", "operator", "viewer"):
            data = _login(client, username, username)
            assert "access_token" in data
            assert "refresh_token" in data


class TestTokenValidation:
    def test_invalid_token_rejected(self, client: TestClient) -> None:
        headers = {"Authorization": "Bearer this-is-not-a-valid-token"}
        resp = client.get("/health", headers=headers)
        assert resp.status_code == 401

    def test_malformed_token_rejected(self, client: TestClient) -> None:
        headers = {"Authorization": "Bearer x.y.z"}
        resp = client.get("/health", headers=headers)
        assert resp.status_code == 401

    def test_expired_token_rejected(self, client: TestClient) -> None:
        expired_payload = {
            "sub": "admin",
            "role": "ADMIN",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "type": "access",
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = client.get("/health", headers=headers)
        assert resp.status_code == 401

    def test_no_token_rejected(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 401

    def test_refresh_token_not_accepted_as_access(self, client: TestClient) -> None:
        data = _login(client, "admin", "admin")
        headers = {"Authorization": f"Bearer {data['refresh_token']}"}
        resp = client.get("/health", headers=headers)
        assert resp.status_code == 401


class TestRefreshToken:
    def test_refresh_success(self, client: TestClient) -> None:
        data = _login(client)
        resp = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert resp.status_code == 200
        new_data = resp.json()
        assert "access_token" in new_data
        assert new_data["access_token"] != data["access_token"]

    def test_refresh_with_invalid_token(self, client: TestClient) -> None:
        resp = client.post("/auth/refresh", json={"refresh_token": "bad-token"})
        assert resp.status_code == 401

    def test_refresh_missing_token(self, client: TestClient) -> None:
        resp = client.post("/auth/refresh", json={})
        assert resp.status_code == 400


class TestRolePermissions:
    def test_admin_can_access_read_endpoints(self, client: TestClient) -> None:
        data = _login(client, "admin", "admin")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        for path in ("/health", "/portfolio", "/trades", "/performance", "/status"):
            resp = client.get(path, headers=headers)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    def test_operator_can_access_read_endpoints(self, client: TestClient) -> None:
        data = _login(client, "operator", "operator")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        for path in ("/health", "/portfolio", "/trades", "/performance", "/status"):
            resp = client.get(path, headers=headers)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    def test_viewer_can_access_read_endpoints(self, client: TestClient) -> None:
        data = _login(client, "viewer", "viewer")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        for path in ("/health", "/portfolio", "/trades", "/performance", "/status"):
            resp = client.get(path, headers=headers)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    def test_admin_can_kill_switch(self, client: TestClient) -> None:
        data = _login(client, "admin", "admin")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp = client.post("/kill-switch", headers=headers)
        assert resp.status_code == 200

    def test_admin_can_resume(self, client: TestClient) -> None:
        data = _login(client, "admin", "admin")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp = client.post("/resume", headers=headers)
        assert resp.status_code == 200

    def test_operator_cannot_kill_switch(self, client: TestClient) -> None:
        data = _login(client, "operator", "operator")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp = client.post("/kill-switch", headers=headers)
        assert resp.status_code == 403

    def test_viewer_cannot_kill_switch(self, client: TestClient) -> None:
        data = _login(client, "viewer", "viewer")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp = client.post("/kill-switch", headers=headers)
        assert resp.status_code == 403


class TestProtectedEndpoints:
    def test_unauthenticated_blocked(self, client: TestClient) -> None:
        for path in ("/health", "/portfolio", "/trades", "/performance", "/status"):
            resp = client.get(path)
            assert resp.status_code == 401, f"{path} returned {resp.status_code}"

    def test_token_from_login_works_on_protected(self, client: TestClient) -> None:
        data = _login(client)
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/status", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["engine"] == "Elite Decision Engine"
