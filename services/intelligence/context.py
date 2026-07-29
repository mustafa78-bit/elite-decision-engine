from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DnaPayload:
    decision_dna_score: float = 0.0
    traits: List[str] = field(default_factory=list)
    signature: Optional[str] = None


@dataclass
class BiasPayload:
    detected_biases: List[str] = field(default_factory=list)
    cognitive_load_index: float = 1.0
    bias_score: float = 0.0


@dataclass
class SimulatorPayload:
    simulated_outcomes: List[Dict[str, Any]] = field(default_factory=list)
    confidence_spread: float = 0.0
    win_probability: float = 0.5


@dataclass
class DebatePayload:
    council_consensus: float = 0.0
    arguments: List[str] = field(default_factory=list)
    debate_duration_ms: float = 0.0


@dataclass
class CounterfactualPayload:
    scenario_scores: Dict[str, float] = field(default_factory=dict)
    best_alternative_action: Optional[str] = None
    expected_value_delta: float = 0.0


@dataclass
class CoachingPayload:
    recommendations: List[str] = field(default_factory=list)
    coaching_tip: Optional[str] = None
    discipline_score: float = 100.0


@dataclass
class MarketMemoryPayload:
    similar_regimes: List[str] = field(default_factory=list)
    historical_similarity_score: float = 0.0
    regime_confidence: float = 0.0


@dataclass
class DecisionMemoryPayload:
    matched_decisions: List[int] = field(default_factory=list)
    success_rate_matched: float = 0.0
    average_matched_pnl: float = 0.0


@dataclass
class PatternPayload:
    pattern_name: Optional[str] = None
    pattern_score: float = 0.0
    is_exceptional: bool = False


@dataclass
class CalibrationPayload:
    expected_calibration_error: float = 0.0
    brier_score: float = 0.0
    confidence_scale_factor: float = 1.0


@dataclass
class DriftPayload:
    drift_detected: bool = False
    psi_score: float = 0.0
    alert_level: str = "NORMAL"


@dataclass
class RiskPayload:
    risk_score: float = 0.0
    max_position_size_usd: float = 10000.0
    allowed: bool = True
    warnings: List[str] = field(default_factory=list)


@dataclass
class UnifiedIntelligenceContext:
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    symbol: str = "BTC"
    market_price: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    service_states: Dict[str, str] = field(default_factory=dict)
    timings: Dict[str, float] = field(default_factory=dict)

    # 12 Subsystem Payload slots
    dna: DnaPayload = field(default_factory=DnaPayload)
    bias: BiasPayload = field(default_factory=BiasPayload)
    simulator: SimulatorPayload = field(default_factory=SimulatorPayload)
    debate: DebatePayload = field(default_factory=DebatePayload)
    counterfactual: CounterfactualPayload = field(default_factory=CounterfactualPayload)
    coaching: CoachingPayload = field(default_factory=CoachingPayload)
    market_memory: MarketMemoryPayload = field(default_factory=MarketMemoryPayload)
    decision_memory: DecisionMemoryPayload = field(default_factory=DecisionMemoryPayload)
    pattern: PatternPayload = field(default_factory=PatternPayload)
    calibration: CalibrationPayload = field(default_factory=CalibrationPayload)
    drift: DriftPayload = field(default_factory=DriftPayload)
    risk: RiskPayload = field(default_factory=RiskPayload)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "market_price": self.market_price,
            "metrics": self.metrics,
            "service_states": self.service_states,
            "timings": self.timings,
            "dna": {
                "decision_dna_score": self.dna.decision_dna_score,
                "traits": self.dna.traits,
                "signature": self.dna.signature,
            },
            "bias": {
                "detected_biases": self.bias.detected_biases,
                "cognitive_load_index": self.bias.cognitive_load_index,
                "bias_score": self.bias.bias_score,
            },
            "simulator": {
                "simulated_outcomes": self.simulator.simulated_outcomes,
                "confidence_spread": self.simulator.confidence_spread,
                "win_probability": self.simulator.win_probability,
            },
            "debate": {
                "council_consensus": self.debate.council_consensus,
                "arguments": self.debate.arguments,
                "debate_duration_ms": self.debate.debate_duration_ms,
            },
            "counterfactual": {
                "scenario_scores": self.counterfactual.scenario_scores,
                "best_alternative_action": self.counterfactual.best_alternative_action,
                "expected_value_delta": self.counterfactual.expected_value_delta,
            },
            "coaching": {
                "recommendations": self.coaching.recommendations,
                "coaching_tip": self.coaching.coaching_tip,
                "discipline_score": self.coaching.discipline_score,
            },
            "market_memory": {
                "similar_regimes": self.market_memory.similar_regimes,
                "historical_similarity_score": self.market_memory.historical_similarity_score,
                "regime_confidence": self.market_memory.regime_confidence,
            },
            "decision_memory": {
                "matched_decisions": self.decision_memory.matched_decisions,
                "success_rate_matched": self.decision_memory.success_rate_matched,
                "average_matched_pnl": self.decision_memory.average_matched_pnl,
            },
            "pattern": {
                "pattern_name": self.pattern.pattern_name,
                "pattern_score": self.pattern.pattern_score,
                "is_exceptional": self.pattern.is_exceptional,
            },
            "calibration": {
                "expected_calibration_error": self.calibration.expected_calibration_error,
                "brier_score": self.calibration.brier_score,
                "confidence_scale_factor": self.calibration.confidence_scale_factor,
            },
            "drift": {
                "drift_detected": self.drift.drift_detected,
                "psi_score": self.drift.psi_score,
                "alert_level": self.drift.alert_level,
            },
            "risk": {
                "risk_score": self.risk.risk_score,
                "max_position_size_usd": self.risk.max_position_size_usd,
                "allowed": self.risk.allowed,
                "warnings": self.risk.warnings,
            },
        }
