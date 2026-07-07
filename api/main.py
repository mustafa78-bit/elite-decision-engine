from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

import config
from core.health_check import HealthCheck
from core.kill_switch import KillSwitch
from database import get_session
from performance_engine import PerformanceEngine
from portfolio_engine import PortfolioEngine

from api.routes.auth import router as auth_router
from api.routes.control import router as control_router
from api.routes.dashboard import router as dashboard_router
from api.routes.health import router as health_router
from api.routes.performance import router as performance_router
from api.routes.portfolio import router as portfolio_router
from api.routes.trades import router as trades_router
from api.routes.ws import router as ws_router
from api.websocket.manager import ConnectionManager
from auth.service import AuthService
from dashboard.metrics import MetricsCollector
from dashboard.service import DashboardService
from risk_manager import RiskManager


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    _app.state.kill_switch = KillSwitch()
    _app.state.health_check = HealthCheck()
    _app.state.portfolio_engine = PortfolioEngine()
    _app.state.performance_engine = PerformanceEngine()
    _app.state.session_factory = get_session
    _app.state.dry_run = getattr(config, "DRY_RUN", True)
    _app.state.trading_mode = "PAPER"
    _app.state.ws_manager = ConnectionManager()
    _app.state.auth_service = AuthService()
    metrics = MetricsCollector()
    _app.state.metrics = metrics
    _app.state.dashboard_service = DashboardService(
        kill_switch=_app.state.kill_switch,
        health_check=_app.state.health_check,
        portfolio_engine=_app.state.portfolio_engine,
        performance_engine=_app.state.performance_engine,
        metrics=metrics,
        session_factory=get_session,
        trading_mode=_app.state.trading_mode,
        dry_run=_app.state.dry_run,
    )
    yield


app = FastAPI(
    title="Elite Decision Engine API",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(portfolio_router)
app.include_router(trades_router)
app.include_router(performance_router)
app.include_router(auth_router)
app.include_router(control_router)
app.include_router(dashboard_router)
app.include_router(ws_router)
