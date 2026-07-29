from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Dict


@dataclass(frozen=True)
class IntelligenceContext:
    symbol: str
    side: str
    market_state: Dict[str, Any] = field(default_factory=dict)
    portfolio_context: Dict[str, Any] = field(default_factory=dict)
    risk_context: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = "corr_default"
    user_id: int = 1
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


@dataclass(frozen=True)
class IntelligenceResult:
    service_name: str
    status: str # SUCCESS, FAILURE, SKIPPED
    confidence: float
    reasoning: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    supporting_signals: List[str] = field(default_factory=list)
    conflicting_signals: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineStarted:
    correlation_id: str
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


@dataclass(frozen=True)
class ServiceStarted:
    correlation_id: str
    service_name: str
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


@dataclass(frozen=True)
class ServiceCompleted:
    correlation_id: str
    service_name: str
    status: str
    duration_ms: float
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


@dataclass(frozen=True)
class ServiceFailed:
    correlation_id: str
    service_name: str
    error_message: str
    duration_ms: float
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


@dataclass(frozen=True)
class PipelineCompleted:
    correlation_id: str
    status: str
    duration_ms: float
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
