"""Elite Terminal API — unified backend for the terminal UI."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from api.dependencies import require_user_id
from services.terminal_service import TerminalService

router = APIRouter()

_service: TerminalService | None = None


def get_terminal() -> TerminalService:
    global _service
    if _service is None:
        _service = TerminalService()
    return _service


@router.get("/terminal/overview")
def terminal_overview(request: Request):
    """Unified overview — market, portfolio, performance, trades, signals, opportunities, risk."""
    user_id = require_user_id(request)
    service = get_terminal()
    return service.get_overview(user_id=user_id)


@router.get("/terminal/market")
def terminal_market():
    """Market health summary."""
    service = get_terminal()
    return service.get_market()


@router.get("/terminal/open-trades")
def terminal_open_trades(request: Request):
    """Currently open trades."""
    user_id = require_user_id(request)
    service = get_terminal()
    return service.get_open_trades(user_id=user_id)


@router.get("/terminal/opportunities")
def terminal_opportunities(n: int = Query(5, ge=1, le=50)):
    """Top scanner opportunities."""
    service = get_terminal()
    return service.get_scanner_opportunities(n=n)


@router.get("/terminal/signals")
def terminal_signals(request: Request, limit: int = Query(10, ge=1, le=100)):
    """Recent trading signals."""
    user_id = require_user_id(request)
    service = get_terminal()
    return service.get_recent_signals(limit=limit, user_id=user_id)


@router.get("/terminal/risk")
def terminal_risk():
    """Risk status overview."""
    service = get_terminal()
    return service.get_risk()


@router.get("/terminal/portfolio")
def terminal_portfolio(request: Request):
    """Portfolio summary."""
    user_id = require_user_id(request)
    service = get_terminal()
    return service.get_portfolio(user_id=user_id)


@router.get("/terminal/performance")
def terminal_performance(request: Request):
    """Performance metrics."""
    user_id = require_user_id(request)
    service = get_terminal()
    return service.get_performance(user_id=user_id)


@router.get("/terminal/decision/{symbol}")
def terminal_decision(symbol: str, timeframe: str = Query("1h")):
    """Full aggregated decision (reasons, warnings, signals, timeline,
    intelligence summary) for a single symbol."""
    service = get_terminal()
    result = service.get_decision(symbol, timeframe)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
    return result
