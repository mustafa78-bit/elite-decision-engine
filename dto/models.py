from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.serialization import SerializableMixin


@dataclass
class PortfolioDTO(SerializableMixin):
    total_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    average_pnl_pct: float = 0.0
    open_trades: int = 0
    largest_win: float = 0.0
    largest_loss: float = 0.0


@dataclass
class TradeDTO(SerializableMixin):
    id: int = 0
    symbol: str = ""
    side: str = ""
    entry_price: float = 0.0
    exit_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = "OPEN"
    created_at: str = ""


@dataclass
class EquityPointDTO(SerializableMixin):
    timestamp: str = ""
    equity: float = 0.0


@dataclass
class PortfolioDetailsDTO:
    summary: PortfolioDTO = field(default_factory=PortfolioDTO)
    equity_curve: List[EquityPointDTO] = field(default_factory=list)
    daily_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    profit_factor: float = 0.0
    exposure: float = 0.0
    asset_allocation: Dict[str, float] = field(default_factory=dict)
    position_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "equity_curve": [e.to_dict() for e in self.equity_curve],
            "daily_pnl": self.daily_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "profit_factor": self.profit_factor,
            "exposure": self.exposure,
            "asset_allocation": dict(self.asset_allocation),
            "position_summary": dict(self.position_summary),
        }


@dataclass
class IntelligenceDTO(SerializableMixin):
    unified_score: float = 50.0
    whale_health: bool = False
    liquidity_health: bool = False
    orderflow_health: bool = False
    ms_health: bool = False
    news_health: bool = False
    sentiment_health: bool = False
    macro_health: bool = False
    module_scores: Dict[str, float] = field(default_factory=dict)
    contribution_report: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketRegimeDTO(SerializableMixin):
    regime: str = "neutral"
    trend: str = "sideways"
    strength: float = 0.0


@dataclass
class IntelligenceDetailsDTO:
    summary: IntelligenceDTO = field(default_factory=IntelligenceDTO)
    ai_confidence: float = 0.0
    funding_summary: Dict[str, Any] = field(default_factory=dict)
    open_interest_summary: Dict[str, Any] = field(default_factory=dict)
    whale_summary: Dict[str, Any] = field(default_factory=dict)
    liquidity_summary: Dict[str, Any] = field(default_factory=dict)
    orderflow_summary: Dict[str, Any] = field(default_factory=dict)
    market_regime: MarketRegimeDTO = field(default_factory=MarketRegimeDTO)
    trend_summary: Dict[str, Any] = field(default_factory=dict)
    signal_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "ai_confidence": self.ai_confidence,
            "funding_summary": dict(self.funding_summary),
            "open_interest_summary": dict(self.open_interest_summary),
            "whale_summary": dict(self.whale_summary),
            "liquidity_summary": dict(self.liquidity_summary),
            "orderflow_summary": dict(self.orderflow_summary),
            "market_regime": self.market_regime.to_dict(),
            "trend_summary": dict(self.trend_summary),
            "signal_summary": dict(self.signal_summary),
        }


@dataclass
class RiskDTO(SerializableMixin):
    risk_score: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    at_risk_trades: int = 0


@dataclass
class MonitoringDTO(SerializableMixin):
    evaluate_calls: int = 0
    modules_active: int = 0
    decisions_today: int = 0
    uptime_hours: float = 0.0
    last_evaluation: str = ""
    memory_usage_mb: float = 0.0


@dataclass
class NotificationDTO(SerializableMixin):
    id: str = ""
    type: str = "info"
    category: str = "general"
    title: str = ""
    message: str = ""
    severity: str = "low"
    priority: int = 0
    read: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AlertSummaryDTO(SerializableMixin):
    total: int = 0
    unread: int = 0
    critical: int = 0
    warning: int = 0
    info: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)


@dataclass
class WidgetDTO(SerializableMixin):
    id: str = ""
    type: str = "metric"
    title: str = ""
    value: Any = None
    change: float = 0.0
    icon: str = ""
    color: str = ""


@dataclass
class KPIDTO(SerializableMixin):
    label: str = ""
    value: float = 0.0
    unit: str = ""
    change: float = 0.0
    trend: str = "neutral"


@dataclass
class DashboardOverviewDTO:
    portfolio: Dict[str, Any] = field(default_factory=dict)
    intelligence: Dict[str, Any] = field(default_factory=dict)
    risk: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    notifications: Dict[str, Any] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "portfolio": dict(self.portfolio),
            "intelligence": dict(self.intelligence),
            "risk": dict(self.risk),
            "monitoring": dict(self.monitoring),
            "notifications": dict(self.notifications),
            "performance": dict(self.performance),
        }


@dataclass
class MarketOverviewDTO(SerializableMixin):
    total_signals: int = 0
    active_modules: int = 0
    module_health: Dict[str, bool] = field(default_factory=dict)
    unified_score: float = 50.0
    market_regime: str = "neutral"


@dataclass
class DashboardMetricsDTO(SerializableMixin):
    cache_hits: int = 0
    cache_misses: int = 0
    cache_size: int = 0
    total_calls: int = 0
    errors: int = 0
    last_refresh: str = ""


@dataclass
class WebSocketDTO(SerializableMixin):
    event: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    version: str = "2.0"


@dataclass
class DashboardDTO:
    portfolio: PortfolioDTO = field(default_factory=PortfolioDTO)
    intelligence: IntelligenceDTO = field(default_factory=IntelligenceDTO)
    risk: RiskDTO = field(default_factory=RiskDTO)
    monitoring: MonitoringDTO = field(default_factory=MonitoringDTO)
    recent_decisions: List[Dict[str, Any]] = field(default_factory=list)
    recent_notifications: List[NotificationDTO] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "portfolio": self.portfolio.to_dict(),
            "intelligence": self.intelligence.to_dict(),
            "risk": self.risk.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "recent_decisions": self.recent_decisions[-20:],
            "recent_notifications": [n.to_dict() for n in self.recent_notifications[-20:]],
        }
