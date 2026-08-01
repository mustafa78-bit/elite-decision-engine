from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from decision.evidence.source_trace import SourceTrace


@dataclass(frozen=True)
class EvidenceItem:
    id: str = ""
    title: str = ""
    description: str = ""
    engine: str = ""
    category: str = ""
    severity: str = "MEDIUM"
    confidence: float = 0.0
    weight: float = 1.0
    supports_decision: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    source: Optional[SourceTrace] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", uuid4().hex[:12])
        if not self.version and self.source:
            object.__setattr__(self, "version", self.source.module_version)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "engine": self.engine,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "weight": self.weight,
            "supports_decision": self.supports_decision,
            "metadata": self.metadata,
            "source": self.source.to_dict() if self.source else None,
            "timestamp": self.timestamp,
            "version": self.version,
        }


@dataclass(frozen=True)
class EvidenceReport:
    recommendation: str = ""
    decision_confidence: float = 0.0
    evidence_strength: float = 0.0
    explainability: float = 0.0
    decision_quality: str = "INSUFFICIENT"
    summary: str = ""
    reasoning: list[str] = field(default_factory=list)
    supporting_evidence: list[EvidenceItem] = field(default_factory=list)
    contradicting_evidence: list[EvidenceItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    timeline: list[EvidenceItem] = field(default_factory=list)
    sources: list[SourceTrace] = field(default_factory=list)
    decision_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.decision_id:
            object.__setattr__(self, "decision_id", uuid4().hex[:12])
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation": self.recommendation,
            "decision_confidence": self.decision_confidence,
            "evidence_strength": self.evidence_strength,
            "explainability": self.explainability,
            "decision_quality": self.decision_quality,
            "summary": self.summary,
            "reasoning": self.reasoning,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [e.to_dict() for e in self.contradicting_evidence],
            "warnings": self.warnings,
            "risk_notes": self.risk_notes,
            "timeline": [e.to_dict() for e in self.timeline],
            "sources": [s.to_dict() for s in self.sources],
            "decision_id": self.decision_id,
            "created_at": self.created_at,
        }
