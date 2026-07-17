from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DecisionFactor:
    name: str
    value: float
    weight: float = 1.0
    source: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def weighted_value(self) -> float:
        return self.value * self.weight


@dataclass
class DecisionContext:
    signal_symbol: str = ""
    signal_side: str = ""
    signal_timeframe: str = ""
    signal_id: int = 0
    base_score: float = 0.0
    factors: List[DecisionFactor] = field(default_factory=list)
    intelligence_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_factor(self, factor: DecisionFactor) -> None:
        self.factors.append(factor)

    def factor_by_name(self, name: str) -> Optional[DecisionFactor]:
        for f in self.factors:
            if f.name == name:
                return f
        return None

    def total_weighted_score(self) -> float:
        if not self.factors:
            return self.base_score
        weighted = sum(f.weighted_value() for f in self.factors)
        total_weight = sum(f.weight for f in self.factors)
        if total_weight == 0:
            return self.base_score
        return weighted / total_weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_symbol": self.signal_symbol,
            "signal_side": self.signal_side,
            "signal_timeframe": self.signal_timeframe,
            "signal_id": self.signal_id,
            "base_score": self.base_score,
            "factors": [f.to_dict() for f in self.factors],
            "total_weighted_score": self.total_weighted_score(),
            "timestamp": self.timestamp.isoformat(),
        }


class DecisionExplanation:
    def __init__(
        self,
        decision: str = "PENDING",
        reasons: Optional[Dict[str, List[str]]] = None,
        confidence_breakdown: Optional[Dict[str, float]] = None,
    ):
        self.decision = decision
        self.reasons = reasons or {"approval": [], "rejection": []}
        self.confidence_breakdown = confidence_breakdown or {}
        self.timestamp = datetime.now(timezone.utc)

    def add_approval_reason(self, reason: str) -> None:
        if reason not in self.reasons["approval"]:
            self.reasons["approval"].append(reason)

    def add_rejection_reason(self, reason: str) -> None:
        if reason not in self.reasons["rejection"]:
            self.reasons["rejection"].append(reason)

    def is_approved(self) -> bool:
        return self.decision == "APPROVED"

    def is_rejected(self) -> bool:
        return self.decision == "REJECTED"

    def summary(self) -> str:
        parts = [f"Decision: {self.decision}"]
        if self.reasons["approval"]:
            parts.append(f"Approval reasons: {'; '.join(self.reasons['approval'])}")
        if self.reasons["rejection"]:
            parts.append(f"Rejection reasons: {'; '.join(self.reasons['rejection'])}")
        if self.confidence_breakdown:
            parts.append(f"Confidence: {self.confidence_breakdown}")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "reasons": dict(self.reasons),
            "confidence_breakdown": dict(self.confidence_breakdown),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DecisionSnapshot:
    signal_id: int
    decision: str
    score: float
    context: DecisionContext
    explanation: Optional[DecisionExplanation] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "decision": self.decision,
            "score": self.score,
            "confidence": self.confidence,
            "context": self.context.to_dict() if self.context else {},
            "explanation": self.explanation.to_dict() if self.explanation else {},
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TradeOutcome:
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    closed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decision_snapshot: Optional[DecisionSnapshot] = None
    strategy_fingerprint: str = ""
    tags: List[str] = field(default_factory=list)

    def is_win(self) -> bool:
        return self.pnl > 0

    def is_loss(self) -> bool:
        return self.pnl < 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "is_win": self.is_win(),
            "is_loss": self.is_loss(),
            "closed_at": self.closed_at.isoformat(),
            "decision_snapshot": self.decision_snapshot.to_dict() if self.decision_snapshot else None,
            "strategy_fingerprint": self.strategy_fingerprint,
            "tags": self.tags,
        }
