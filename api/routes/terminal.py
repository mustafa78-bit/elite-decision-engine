"""Elite Terminal API — unified backend for the terminal UI."""

from __future__ import annotations

from fastapi import APIRouter, Query

from services.terminal_service import TerminalService

router = APIRouter()

_service: TerminalService | None = None


def get_terminal() -> TerminalService:
    global _service
    if _service is None:
        _service = TerminalService()
    return _service


@router.get("/terminal/overview")
def terminal_overview():
    """Unified overview — market, portfolio, performance, trades, signals, opportunities, risk."""
    service = get_terminal()
    return service.get_overview()


@router.get("/terminal/market")
def terminal_market():
    """Market health summary."""
    service = get_terminal()
    return service.get_market()


@router.get("/terminal/open-trades")
def terminal_open_trades():
    """Currently open trades."""
    service = get_terminal()
    return service.get_open_trades()


@router.get("/terminal/opportunities")
def terminal_opportunities(n: int = Query(5, ge=1, le=50)):
    """Top scanner opportunities."""
    service = get_terminal()
    return service.get_scanner_opportunities(n=n)


@router.get("/terminal/signals")
def terminal_signals(limit: int = Query(10, ge=1, le=100)):
    """Recent trading signals."""
    service = get_terminal()
    return service.get_recent_signals(limit=limit)


@router.get("/terminal/risk")
def terminal_risk():
    """Risk status overview."""
    service = get_terminal()
    return service.get_risk()


@router.get("/terminal/portfolio")
def terminal_portfolio():
    """Portfolio summary."""
    service = get_terminal()
    return service.get_portfolio()


@router.get("/terminal/performance")
def terminal_performance():
    """Performance metrics."""
    service = get_terminal()
    return service.get_performance()
