from __future__ import annotations

import logging
from services.intelligence.context import UnifiedIntelligenceContext

logger = logging.getLogger(__name__)


class OpportunityRankingEngine:
    """Calculates the normalized Executive Opportunity Score [0.0 - 100.0]

    by evaluating and combining multiple platform intelligence signals.
    """

    def calculate_score(self, context: UnifiedIntelligenceContext) -> float:
        """Determines the composite opportunity score using weighted intelligence inputs."""
        weights = {
            "technical": 0.20,
            "risk": 0.15,
            "memory": 0.15,
            "pattern": 0.10,
            "debate": 0.15,
            "counterfactual": 0.10,
            "calibration": 0.10,
            "drift": 0.05,
        }

        # 1. Technical Strength (Pattern score or fallback)
        tech_score = context.pattern.pattern_score if context.pattern.pattern_score > 0 else 50.0

        # 2. Risk Profile (Lower risk score yields higher opportunity)
        risk_score = max(0.0, min(100.0, context.risk.risk_score))
        risk_opp = 100.0 - risk_score

        # 3. Decision Memory Similarity (Success rate matched)
        mem_score = context.decision_memory.success_rate_matched if context.decision_memory.success_rate_matched > 0 else 50.0

        # 4. Pattern Discovery confidence
        pattern_score = context.pattern.pattern_score if context.pattern.pattern_score > 0 else 50.0

        # 5. AI Debate outcome (Council consensus)
        debate_score = context.debate.council_consensus if context.debate.council_consensus > 0 else 50.0

        # 6. Counterfactual Analysis
        counterfactual_opp = min(100.0, context.counterfactual.expected_value_delta * 5.0)  # scale delta

        # 7. Confidence Calibration (Penalty for high Expected Calibration Error)
        ece = context.calibration.expected_calibration_error
        calibration_score = max(0.0, 100.0 - (ece * 200.0))  # penalize large ECE

        # 8. Drift status (Penalty for high PSI score)
        psi = context.drift.psi_score
        drift_score = max(0.0, 100.0 - (psi * 300.0))  # penalize large drift index

        # Compute weighted sum
        weighted_sum = (
            tech_score * weights["technical"] +
            risk_opp * weights["risk"] +
            mem_score * weights["memory"] +
            pattern_score * weights["pattern"] +
            debate_score * weights["debate"] +
            counterfactual_opp * weights["counterfactual"] +
            calibration_score * weights["calibration"] +
            drift_score * weights["drift"]
        )

        final_score = max(0.0, min(100.0, weighted_sum))
        logger.info("Computed Executive Opportunity Score for %s: %.2f", context.symbol, final_score)
        return round(final_score, 2)
