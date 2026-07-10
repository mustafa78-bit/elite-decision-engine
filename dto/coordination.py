from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class IntelligenceSourceDTO:
    name: str = ""
    source_type: str = ""
    confidence: float = 0.0
    weight: float = 1.0
    available: bool = False
    last_updated: str = ""
    latency_ms: float = 0.0
    error_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConfidenceAggregationDTO:
    source_name: str = ""
    raw_confidence: float = 0.0
    weighted_confidence: float = 0.0
    weight: float = 1.0
    adjusted: bool = False
    adjustment_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConflictResolutionDTO:
    source_a: str = ""
    source_b: str = ""
    value_a: float = 0.0
    value_b: float = 0.0
    resolved_value: float = 0.0
    resolution_strategy: str = ""
    resolution_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsensusScoreDTO:
    final_score: float = 0.0
    agreement_level: str = ""
    source_count: int = 0
    sources_agreeing: int = 0
    sources_disagreeing: int = 0
    variance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourcePriorityDTO:
    source_name: str = ""
    priority: int = 0
    weight: float = 1.0
    is_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecommendationRankingDTO:
    rank: int = 0
    signal_id: int = 0
    symbol: str = ""
    side: str = ""
    composite_score: float = 0.0
    recommendation: str = ""
    reasons: list[str] = field(default_factory=list)
    sources_evaluated: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CoordinatorDiagnosticsDTO:
    total_evaluations: int = 0
    total_conflicts: int = 0
    conflicts_resolved: int = 0
    avg_processing_time_ms: float = 0.0
    source_availability: dict[str, bool] = field(default_factory=dict)
    source_latency: dict[str, float] = field(default_factory=dict)
    errors_last_hour: int = 0
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CoordinatorReportDTO:
    consensus: Optional[ConsensusScoreDTO] = None
    aggregations: list[ConfidenceAggregationDTO] = field(default_factory=list)
    conflicts: list[ConflictResolutionDTO] = field(default_factory=list)
    priorities: list[SourcePriorityDTO] = field(default_factory=list)
    recommendations: list[RecommendationRankingDTO] = field(default_factory=list)
    diagnostics: Optional[CoordinatorDiagnosticsDTO] = None

    def to_dict(self) -> dict[str, Any]:
        d = {}
        for key in ("aggregations", "conflicts", "priorities", "recommendations"):
            items = getattr(self, key, [])
            d[key] = [i.to_dict() if hasattr(i, "to_dict") else asdict(i) for i in items]
        for key in ("consensus", "diagnostics"):
            val = getattr(self, key, None)
            d[key] = val.to_dict() if val else None
        return d
