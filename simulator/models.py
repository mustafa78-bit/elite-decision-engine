from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SimStatus(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"


class SimSpeed(StrEnum):
    SPEED_1X = "1x"
    SPEED_2X = "2x"
    SPEED_5X = "5x"
    SPEED_10X = "10x"
    SPEED_100X = "100x"
    UNLIMITED = "unlimited"


class AIDecisionMode(StrEnum):
    MANUAL = "MANUAL"
    AI_ASSISTED = "AI_ASSISTED"
    FULL_AI = "FULL_AI"


class ScenarioType(StrEnum):
    FLASH_CRASH = "FLASH_CRASH"
    BULL_RUN = "BULL_RUN"
    CAPITULATION = "CAPITULATION"
    RANGE = "RANGE"
    WHALE_ACCUMULATION = "WHALE_ACCUMULATION"
    WHALE_DISTRIBUTION = "WHALE_DISTRIBUTION"
    ETF_NEWS = "ETF_NEWS"
    EXCHANGE_LISTING = "EXCHANGE_LISTING"
    BLACK_SWAN = "BLACK_SWAN"
    CUSTOM = "CUSTOM"


class MarketRegime(StrEnum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"


@dataclass
class SimulatorConfig:
    symbol: str = "BTC"
    timeframe: str = "1h"
    start_date: str | None = None
    end_date: str | None = None
    initial_capital: float = 10000.0
    ai_mode: AIDecisionMode = AIDecisionMode.FULL_AI
    speed: SimSpeed = SimSpeed.SPEED_1X
    scenario: ScenarioType | None = None
    slippage_bps: int = 5
    fee_rate: float = 0.001
    leverage: float = 1.0
    risk_per_trade: float = 0.02
    founder_mode: bool = False
    whale_simulation: bool = False
    news_replay: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SimulatorConfig:
        if "ai_mode" in d and isinstance(d["ai_mode"], str):
            d["ai_mode"] = AIDecisionMode(d["ai_mode"])
        if "speed" in d and isinstance(d["speed"], str):
            d["speed"] = SimSpeed(d["speed"])
        if "scenario" in d and isinstance(d["scenario"], str) and d["scenario"]:
            d["scenario"] = ScenarioType(d["scenario"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SimulatedCandle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SimulatedCandle:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SimulatedDecision:
    id: str
    symbol: str
    side: str
    timestamp: int
    price: float
    decision: str
    confidence: float
    evidence_strength: float
    risk_score: float
    council_report: dict[str, Any] | None = None
    evidence_report: dict[str, Any] | None = None
    explanation: dict[str, Any] | None = None
    agent_reports: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SimulatedDecision:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SimulatedTrade:
    id: str
    symbol: str
    side: str
    entry_price: float
    entry_time: int
    quantity: float
    leverage: float
    stop_loss: float
    take_profit: float
    trailing_stop: float | None = None
    trailing_stop_peak: float | None = None
    status: str = "OPEN"
    exit_price: float | None = None
    exit_time: int | None = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    close_reason: str | None = None
    decision_id: str | None = None
    elite_score: float | None = None
    entry_decision: dict[str, Any] | None = None
    exit_decision: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SimulatedTrade:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class TimelineEvent:
    id: str
    timestamp: int
    event_type: str
    symbol: str
    title: str
    description: str
    severity: str = "info"
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TimelineEvent:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class TrainingScore:
    patience: float = 0.0
    risk: float = 0.0
    timing: float = 0.0
    entry_quality: float = 0.0
    exit_quality: float = 0.0
    psychology: float = 0.0
    discipline: float = 0.0
    missed_trades: int = 0
    mistakes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EliteScore:
    overall: float = 0.0
    confidence: float = 0.0
    evidence_strength: float = 0.0
    risk: float = 0.0
    execution: float = 0.0
    reward: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SimulatorState:
    session_id: str
    status: SimStatus = SimStatus.IDLE
    config: SimulatorConfig = field(default_factory=SimulatorConfig)
    current_candle_index: int = 0
    total_candles: int = 0
    current_timestamp: int | None = None
    current_price: float | None = None
    elapsed_seconds: float = 0.0
    candles: list[SimulatedCandle] = field(default_factory=list)
    decisions: list[SimulatedDecision] = field(default_factory=list)
    trades: list[SimulatedTrade] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)
    regime: MarketRegime = MarketRegime.SIDEWAYS
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    portfolio_value: float = 10000.0
    cash: float = 10000.0
    open_positions: int = 0
    total_pnl: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    founder_metrics: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["regime"] = self.regime.value
        d["config"] = self.config.to_dict()
        return d


@dataclass
class SessionMeta:
    id: str
    name: str
    created_at: str
    updated_at: str
    config: SimulatorConfig
    status: SimStatus = SimStatus.IDLE
    total_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["config"] = self.config.to_dict()
        return d


@dataclass
class MissionReport:
    session_id: str
    config: SimulatorConfig
    duration_seconds: float
    total_candles: int
    total_decisions: int
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    total_fees: float
    total_slippage: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_holding_time: float
    final_portfolio_value: float
    return_pct: float
    regime_changes: list[dict[str, Any]]
    elite_scores: list[EliteScore]
    training_score: TrainingScore
    trades: list[SimulatedTrade]
    decisions: list[SimulatedDecision]
    timeline: list[TimelineEvent]
    equity_curve: list[dict[str, Any]]
    mistakes: list[str]
    lessons: list[str]
    ai_recommendations: list[str]
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["config"] = self.config.to_dict()
        d["elite_scores"] = [s.to_dict() for s in self.elite_scores]
        d["training_score"] = self.training_score.to_dict()
        return d
