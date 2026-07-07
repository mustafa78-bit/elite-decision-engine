from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.routes.control import router as control_router
from api.routes.health import router as health_router
from api.routes.performance import router as performance_router
from api.routes.portfolio import router as portfolio_router
from api.routes.trades import router as trades_router
from core.health_check import HealthReport, HealthStatus
from core.kill_switch import KillSwitch


@pytest.fixture
def app() -> FastAPI:
    _app = FastAPI()
    _app.state.kill_switch = KillSwitch()
    _app.state.health_check = MagicMock()
    _app.state.portfolio_engine = MagicMock()
    _app.state.performance_engine = MagicMock()
    _app.state.session_factory = MagicMock()
    _app.state.dry_run = True
    _app.state.trading_mode = "PAPER"
    _app.include_router(health_router)
    _app.include_router(portfolio_router)
    _app.include_router(trades_router)
    _app.include_router(performance_router)
    _app.include_router(control_router)
    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestStatus:
    def test_get_status_default(self, client: TestClient):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["kill_switch"] == "RUNNING"
        assert data["running"] is True
        assert data["dry_run"] is True
        assert data["trading_mode"] == "PAPER"
        assert data["engine"] == "Elite Decision Engine"

    def test_get_status_after_kill_switch(self, client: TestClient):
        client.post("/kill-switch")
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["kill_switch"] == "STOPPED"
        assert data["running"] is False

    def test_get_status_after_resume(self, client: TestClient):
        client.post("/kill-switch")
        client.post("/resume")
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["kill_switch"] == "RUNNING"
        assert data["running"] is True


class TestHealth:
    def test_health_healthy(self, client: TestClient, app: FastAPI):
        app.state.health_check.run.return_value = HealthReport(
            overall_status=HealthStatus.HEALTHY,
            checks={"database": HealthStatus.HEALTHY, "logging": HealthStatus.HEALTHY},
            duration_ms=5.0,
        )
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall"] == "HEALTHY"
        assert data["checks"]["database"] == "HEALTHY"
        assert isinstance(data["duration_ms"], float)

    def test_health_failed(self, client: TestClient, app: FastAPI):
        app.state.health_check.run.return_value = HealthReport(
            overall_status=HealthStatus.FAILED,
            checks={"database": HealthStatus.FAILED},
            errors=["Database connection failed"],
            duration_ms=10.0,
        )
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall"] == "FAILED"
        assert "Database connection failed" in data["errors"]


class TestPortfolio:
    def test_portfolio(self, client: TestClient, app: FastAPI):
        mock_stats = MagicMock()
        mock_stats.total_trades = 10
        mock_stats.open_trades = 3
        mock_stats.closed_trades = 7
        mock_stats.winning_trades = 4
        mock_stats.losing_trades = 3
        mock_stats.win_rate = 57.14
        mock_stats.total_pnl = 500.0
        mock_stats.daily_pnl = 100.0
        mock_stats.average_win = 200.0
        mock_stats.average_loss = -100.0
        mock_stats.profit_factor = 2.5
        mock_stats.max_drawdown = 15.0
        mock_stats.current_open_exposure = 30000.0
        app.state.portfolio_engine.stats.return_value = mock_stats

        resp = client.get("/portfolio")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_trades"] == 10
        assert data["open_trades"] == 3
        assert data["win_rate"] == 57.14
        assert data["total_pnl"] == 500.0


class TestTrades:
    def test_trades_empty(self, client: TestClient, app: FastAPI):
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.side_effect = [[], []]
        mock_session.query.return_value = mock_query
        app.state.session_factory.return_value = mock_session

        resp = client.get("/trades")
        assert resp.status_code == 200
        data = resp.json()
        assert data["open"] == []
        assert data["closed"] == []

    def test_trades_with_data(self, client: TestClient, app: FastAPI):
        open_trade = MagicMock()
        open_trade.id = 1
        open_trade.symbol = "BTCUSDT"
        open_trade.side = "LONG"
        open_trade.entry = 50000.0
        open_trade.pnl = 0.0
        open_trade.status = "OPEN"
        open_trade.close_reason = None
        open_trade.exit_price = None

        closed_trade = MagicMock()
        closed_trade.id = 2
        closed_trade.symbol = "ETHUSDT"
        closed_trade.side = "SHORT"
        closed_trade.entry = 3000.0
        closed_trade.pnl = 150.0
        closed_trade.status = "TP_HIT"
        closed_trade.close_reason = "TP_HIT"
        closed_trade.exit_price = 2800.0

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.side_effect = [[open_trade], [closed_trade]]
        mock_session.query.return_value = mock_query
        app.state.session_factory.return_value = mock_session

        resp = client.get("/trades")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["open"]) == 1
        assert data["open"][0]["symbol"] == "BTCUSDT"
        assert data["open"][0]["close_reason"] is None
        assert data["open"][0]["exit_price"] is None
        assert len(data["closed"]) == 1
        assert data["closed"][0]["symbol"] == "ETHUSDT"
        assert data["closed"][0]["pnl"] == 150.0
        assert data["closed"][0]["close_reason"] == "TP_HIT"
        assert data["closed"][0]["exit_price"] == 2800.0


class TestPerformance:
    def test_performance(self, client: TestClient, app: FastAPI):
        mock_stats = MagicMock()
        mock_stats.sharpe_ratio = 1.5
        mock_stats.sortino_ratio = 2.0
        mock_stats.profit_factor = 2.5
        mock_stats.expectancy = 50.0
        mock_stats.recovery_factor = 3.0
        mock_stats.calmar_ratio = 0.5
        mock_stats.average_r_multiple = 1.2
        mock_stats.average_holding_hours = 24.0
        mock_stats.consecutive_wins = 3
        mock_stats.consecutive_losses = 2
        mock_stats.best_trade = 500.0
        mock_stats.worst_trade = -100.0
        app.state.performance_engine.stats.return_value = mock_stats

        resp = client.get("/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sharpe_ratio"] == 1.5
        assert data["consecutive_wins"] == 3
        assert data["best_trade"] == 500.0
        assert data["worst_trade"] == -100.0


class TestControl:
    def test_kill_switch_disables(self, client: TestClient):
        resp = client.post("/kill-switch")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "disabled" in data["message"].lower()

    def test_resume(self, client: TestClient):
        client.post("/kill-switch")
        resp = client.post("/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_kill_switch_then_status(self, client: TestClient):
        resp_before = client.get("/status")
        assert resp_before.json()["running"] is True

        client.post("/kill-switch")
        resp_after = client.get("/status")
        assert resp_after.json()["running"] is False

        client.post("/resume")
        resp_resumed = client.get("/status")
        assert resp_resumed.json()["running"] is True
