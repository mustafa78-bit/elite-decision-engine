from __future__ import annotations

from pydantic import BaseModel


class StatusResponse(BaseModel):
    engine: str = "Elite Decision Engine"
    kill_switch: str
    running: bool
    dry_run: bool
    trading_mode: str


class HealthCheckResponse(BaseModel):
    overall: str
    duration_ms: float
    checks: dict[str, str]
    warnings: list[str]
    errors: list[str]


class TradeItem(BaseModel):
    id: int
    symbol: str
    side: str
    entry: float
    pnl: float
    status: str
    close_reason: str | None = None
    exit_price: float | None = None


class TradesResponse(BaseModel):
    open: list[TradeItem]
    closed: list[TradeItem]


class PortfolioResponse(BaseModel):
    total_trades: int
    open_trades: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    daily_pnl: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    current_open_exposure: float


class PerformanceResponse(BaseModel):
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    expectancy: float
    recovery_factor: float
    calmar_ratio: float
    average_r_multiple: float
    average_holding_hours: float
    consecutive_wins: int
    consecutive_losses: int
    best_trade: float
    worst_trade: float
