from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, PropertyMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.dependencies import get_current_user, require_admin, require_read
from api.routes.dashboard import router as dashboard_router
from core.health_check import HealthReport, HealthStatus
from core.kill_switch import KillSwitch
from dashboard.metrics import MetricsCollector
from dashboard.schemas import (
    ActivityResponse,
    OverviewResponse,
    PortfolioSummaryResponse,
    RiskSummaryResponse,
    StatsResponse,
)
from dashboard.service import DashboardService
from performance_engine import PerformanceStats
from portfolio_engine import PortfolioStats


@pytest.fixture
def mock_portfolio_stats() -> MagicMock:
    stats = MagicMock(spec=PortfolioStats)
    stats.total_trades = 10
    stats.open_trades = 2
    stats.closed_trades = 8
    stats.winning_trades = 5
    stats.losing_trades = 3
    stats.win_rate = 62.5
    stats.total_pnl = 1500.0
    stats.daily_pnl = 200.0
    stats.average_win = 400.0
    stats.average_loss = -150.0
    stats.profit_factor = 2.5
    stats.max_drawdown = 12.0
    stats.current_open_exposure = 50000.0
    stats.equity_curve = [10000.0, 10500.0]
    return stats


@pytest.fixture
def mock_perf_stats() -> MagicMock:
    stats = MagicMock(spec=PerformanceStats)
    stats.sharpe_ratio = 1.5
    stats.sortino_ratio = 2.0
    stats.profit_factor = 2.5
    stats.expectancy = 50.0
    stats.recovery_factor = 3.0
    stats.calmar_ratio = 0.5
    stats.average_r_multiple = 1.2
    stats.average_holding_hours = 24.0
    stats.consecutive_wins = 3
    stats.consecutive_losses = 2
    stats.best_trade = 500.0
    stats.worst_trade = -100.0
    return stats


@pytest.fixture
def mock_session() -> MagicMock:
    from datetime import datetime, timezone

    session = MagicMock()
    query = MagicMock()

    now = datetime.now(timezone.utc)

    mock_trade = MagicMock()
    mock_trade.id = 1
    mock_trade.symbol = "BTCUSDT"
    mock_trade.side = "LONG"
    mock_trade.status = "OPEN"
    mock_trade.entry = 50000.0
    mock_trade.pnl = 0.0
    mock_trade.created_at = now

    mock_signal = MagicMock()
    mock_signal.symbol = "ETHUSDT"
    mock_signal.side = "SHORT"
    mock_signal.score = 90.0
    mock_signal.created_at = now

    query.filter.return_value.all.return_value = []
    query.order_by.return_value.limit.return_value.all.side_effect = [
        [mock_trade],
        [mock_signal],
    ]
    session.query.return_value = query
    return session


@pytest.fixture
def app(
    mock_portfolio_stats: MagicMock,
    mock_perf_stats: MagicMock,
    mock_session: MagicMock,
) -> FastAPI:
    _app = FastAPI()
    _app.state.kill_switch = KillSwitch()
    _app.state.health_check = MagicMock()
    _app.state.health_check.run.return_value = HealthReport(
        overall_status=HealthStatus.HEALTHY,
        checks={"database": HealthStatus.HEALTHY},
        duration_ms=5.0,
    )

    pe = MagicMock()
    pe.stats.return_value = mock_portfolio_stats
    _app.state.portfolio_engine = pe

    pfe = MagicMock()
    pfe.stats.return_value = mock_perf_stats
    _app.state.performance_engine = pfe

    _app.state.session_factory = MagicMock(return_value=mock_session)
    _app.state.dry_run = True
    _app.state.trading_mode = "PAPER"
    _app.state.ws_manager = MagicMock()

    _app.state.dashboard_service = DashboardService(
        kill_switch=_app.state.kill_switch,
        health_check=_app.state.health_check,
        portfolio_engine=pe,
        performance_engine=pfe,
        metrics=MetricsCollector(),
        session_factory=_app.state.session_factory,
        trading_mode=_app.state.trading_mode,
        dry_run=_app.state.dry_run,
    )

    _app.include_router(dashboard_router)

    async def _mock_user() -> dict[str, Any]:
        return {"sub": "admin", "role": "ADMIN"}

    _app.dependency_overrides[get_current_user] = _mock_user
    _app.dependency_overrides[require_admin] = _mock_user
    _app.dependency_overrides[require_read] = _mock_user
    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestDashboardService:
    def test_overview(self, mock_portfolio_stats: MagicMock) -> None:
        ks = KillSwitch()
        svc = DashboardService(
            kill_switch=ks,
            health_check=MagicMock(),
            portfolio_engine=MagicMock(),
            performance_engine=MagicMock(),
            metrics=MetricsCollector(),
            session_factory=MagicMock(),
        )
        svc._portfolio_engine.stats.return_value = mock_portfolio_stats
        result = svc.overview()
        assert isinstance(result, OverviewResponse)
        assert result.engine_status == "RUNNING"
        assert result.mode == "PAPER"
        assert result.open_trades == 2
        assert result.risk_level == "MEDIUM"

    def test_stats(self, mock_portfolio_stats: MagicMock, mock_perf_stats: MagicMock) -> None:
        svc = DashboardService(
            kill_switch=MagicMock(),
            health_check=MagicMock(),
            portfolio_engine=MagicMock(),
            performance_engine=MagicMock(),
            metrics=MetricsCollector(),
            session_factory=MagicMock(),
        )
        svc._portfolio_engine.stats.return_value = mock_portfolio_stats
        svc._performance_engine.stats.return_value = mock_perf_stats
        result = svc.stats()
        assert isinstance(result, StatsResponse)
        assert result.total_trades == 10
        assert result.win_rate == 62.5
        assert result.pnl == 1500.0
        assert result.average_return == 150.0

    def test_portfolio(self, mock_portfolio_stats: MagicMock) -> None:
        svc = DashboardService(
            kill_switch=MagicMock(),
            health_check=MagicMock(),
            portfolio_engine=MagicMock(),
            performance_engine=MagicMock(),
            metrics=MetricsCollector(),
            session_factory=MagicMock(),
        )
        svc._portfolio_engine.stats.return_value = mock_portfolio_stats
        result = svc.portfolio()
        assert isinstance(result, PortfolioSummaryResponse)
        assert result.equity == 11500.0
        assert result.exposure == 50000.0
        assert result.open_positions == 2

    def test_activity_empty(self) -> None:
        mock_sesh = MagicMock()
        query = MagicMock()
        query.order_by.return_value.limit.return_value.all.return_value = []
        mock_sesh.query.return_value = query

        svc = DashboardService(
            kill_switch=MagicMock(),
            health_check=MagicMock(),
            portfolio_engine=MagicMock(),
            performance_engine=MagicMock(),
            metrics=MetricsCollector(),
            session_factory=MagicMock(return_value=mock_sesh),
        )
        result = svc.activity()
        assert isinstance(result, ActivityResponse)
        assert result.activities == []

    def test_metrics(self) -> None:
        metrics = MetricsCollector()
        assert metrics.request_count == 0
        assert metrics.uptime_seconds >= 0
        metrics.increment_requests()
        assert metrics.request_count == 1
        snap = metrics.snapshot()
        assert "uptime_seconds" in snap
        assert snap["request_count"] == 1


class TestDashboardEndpoints:
    def test_overview_endpoint(self, client: TestClient) -> None:
        resp = client.get("/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["engine_status"] == "RUNNING"
        assert data["mode"] == "PAPER"
        assert data["open_trades"] == 2
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    def test_stats_endpoint(self, client: TestClient) -> None:
        resp = client.get("/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_trades"] == 10
        assert data["win_rate"] == 62.5
        assert data["pnl"] == 1500.0

    def test_portfolio_endpoint(self, client: TestClient) -> None:
        resp = client.get("/dashboard/portfolio")
        assert resp.status_code == 200
        data = resp.json()
        assert data["equity"] == 11500.0
        assert data["exposure"] == 50000.0
        assert data["open_positions"] == 2
        assert data["available_balance"] <= data["equity"]

    def test_risk_endpoint(self, client: TestClient) -> None:
        resp = client.get("/dashboard/risk")
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_status" in data
        assert "position_limits" in data
        assert "exposure" in data

    def test_activity_endpoint(self, client: TestClient) -> None:
        resp = client.get("/dashboard/activity")
        assert resp.status_code == 200
        data = resp.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)


class TestDashboardAuth:
    def test_no_auth_returns_401(self, app: FastAPI) -> None:
        app.dependency_overrides.clear()
        client = TestClient(app)
        resp = client.get("/dashboard/overview")
        assert resp.status_code == 401

    def test_operator_can_access(self, app: FastAPI) -> None:
        async def _operator() -> dict[str, Any]:
            return {"sub": "operator", "role": "OPERATOR"}

        app.dependency_overrides[get_current_user] = _operator
        app.dependency_overrides[require_read] = _operator
        client = TestClient(app)

        for path in (
            "/dashboard/overview",
            "/dashboard/stats",
            "/dashboard/portfolio",
            "/dashboard/risk",
            "/dashboard/activity",
        ):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    def test_viewer_can_access(self, app: FastAPI) -> None:
        async def _viewer() -> dict[str, Any]:
            return {"sub": "viewer", "role": "VIEWER"}

        app.dependency_overrides[get_current_user] = _viewer
        app.dependency_overrides[require_read] = _viewer
        client = TestClient(app)

        resp = client.get("/dashboard/overview")
        assert resp.status_code == 200
