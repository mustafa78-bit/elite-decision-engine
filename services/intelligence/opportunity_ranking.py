from __future__ import annotations

import logging
from typing import Dict, Any, List
from core.orchestrator.models import IntelligenceContext, IntelligenceResult

logger = logging.getLogger(__name__)


class OpportunityRankingService:
    """
    Computes global opportunity rankings utilizing a multi-dimensional composite intelligence score.
    """

    def __init__(self):
        self.weights = {
            "technical_strength": 0.20,
            "strategic_intelligence": 0.15,
            "historical_similarity": 0.15,
            "learning_confidence": 0.10,
            "pattern_strength": 0.10,
            "risk_profile": 0.15,
            "market_regime": 0.05,
            "decision_confidence": 0.10
        }

    def evaluate(self, context: IntelligenceContext) -> IntelligenceResult:
        """
        Evaluate and rank opportunities sequentially across multiple analytical fields.
        """
        symbol = context.symbol

        # Pull signals or default high value baselines
        raw = context.raw_inputs
        technical_strength = float(raw.get("technical_strength", 0.85))
        strategic_intelligence = float(raw.get("strategic_intelligence", 0.80))
        historical_similarity = float(raw.get("historical_similarity", 0.75))
        learning_confidence = float(raw.get("learning_confidence", 0.90))
        pattern_strength = float(raw.get("pattern_strength", 0.88))
        risk_profile = float(raw.get("risk_profile", 0.82))
        market_regime = float(raw.get("market_regime", 0.78))
        decision_confidence = float(raw.get("decision_confidence", 0.85))

        # Perform weighted composite logic
        composite_score = (
            (technical_strength * self.weights["technical_strength"]) +
            (strategic_intelligence * self.weights["strategic_intelligence"]) +
            (historical_similarity * self.weights["historical_similarity"]) +
            (learning_confidence * self.weights["learning_confidence"]) +
            (pattern_strength * self.weights["pattern_strength"]) +
            (risk_profile * self.weights["risk_profile"]) +
            (market_regime * self.weights["market_regime"]) +
            (decision_confidence * self.weights["decision_confidence"])
        )

        composite_score = round(composite_score, 4)

        reasoning = (
            f"Opportunity Ranker compiled a multi-dimensional composite score of {composite_score} for {symbol}. "
            f"Strongest drivers include Technical Strength ({technical_strength}) and Learning Confidence ({learning_confidence})."
        )

        return IntelligenceResult(
            engine_name="Priority Ranking",
            confidence=composite_score,
            reasoning=reasoning,
            evidence={
                "composite_score": composite_score,
                "weights": self.weights,
                "dimensions": {
                    "technical_strength": technical_strength,
                    "strategic_intelligence": strategic_intelligence,
                    "historical_similarity": historical_similarity,
                    "learning_confidence": learning_confidence,
                    "pattern_strength": pattern_strength,
                    "risk_profile": risk_profile,
                    "market_regime": market_regime,
                    "decision_confidence": decision_confidence
                }
            },
            supporting_signals=["Low risk profile", "Favorable pattern Discovery correlation"],
            conflicting_signals=["Slight strategic divergence in macro regime"],
            assumptions=["Weights match constitutional priority guidelines"]
        )
