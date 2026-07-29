from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from services.dna_service import DecisionDNAService
from database import get_session

logger = logging.getLogger(__name__)


class DecisionSimulatorService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.dna_service = DecisionDNAService(session_factory=self.session_factory)

    def simulate_decision(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        user_id: int = 1,
    ) -> dict[str, Any]:

        # 1. Consume DNA profile to adjust simulation context
        dna = self.dna_service.get_or_create_profile(user_id)

        # 2. Risk/Reward ratio calculation
        risk_dist = abs(entry_price - stop_loss)
        reward_dist = abs(take_profit - entry_price)
        rr_ratio = reward_dist / risk_dist if risk_dist > 0 else 1.0

        # 3. Simulate expected outcome and confidence
        expected_risk_usd = position_size * (risk_dist / entry_price) if entry_price > 0 else 0.0
        expected_reward_usd = position_size * (reward_dist / entry_price) if entry_price > 0 else 0.0

        # Simulation confidence score base
        sim_confidence = 80.0
        primary_risks = []
        supporting_evidence = []
        alternative_outcomes = []

        # Consume DNA traits
        if dna.risk_profile == "CONSERVATIVE" and expected_risk_usd > 1000.0:
            primary_risks.append("Position size exceeds Conservative user risk profile threshold.")
            sim_confidence -= 10.0
        elif dna.risk_profile == "AGGRESSIVE":
            sim_confidence += 5.0

        if rr_ratio < 1.5:
            primary_risks.append("Risk/Reward ratio is sub-optimal (< 1.5).")
            sim_confidence -= 15.0
        else:
            supporting_evidence.append(f"Risk/Reward ratio is strong ({round(rr_ratio, 2)}).")

        supporting_evidence.append(f"Aligned with preferred strategies: {', '.join(dna.preferred_strategies or [])}")

        # Alternative outcomes simulation
        # Scenario A: Tight stop pullback
        tight_stop = entry_price - (risk_dist * 0.5) if side == "LONG" else entry_price + (risk_dist * 0.5)
        tight_risk_usd = expected_risk_usd * 0.5
        alternative_outcomes.append({
            "scenario": "TIGHT_STOP",
            "stop_loss": round(tight_stop, 2),
            "expected_risk_usd": round(tight_risk_usd, 2),
            "probability": "HIGH"
        })

        # Scenario B: Partial take profit at 50% reward
        partial_tp = entry_price + (reward_dist * 0.5) if side == "LONG" else entry_price - (reward_dist * 0.5)
        alternative_outcomes.append({
            "scenario": "PARTIAL_TP",
            "take_profit": round(partial_tp, 2),
            "expected_reward_usd": round(expected_reward_usd * 0.5, 2),
            "probability": "MEDIUM"
        })

        sim_confidence = max(10.0, min(100.0, sim_confidence))

        # Telemetry
        logger.info(
            "TELEMETRY: [DecisionSimulator] Simulated decision for user %s on %s with base confidence %s%%",
            user_id, symbol, sim_confidence
        )

        return {
            "symbol": symbol,
            "side": side,
            "expected_outcome": "PROFIT" if rr_ratio >= 1.5 else "LOSS",
            "confidence": round(sim_confidence, 1),
            "expected_risk_usd": round(expected_risk_usd, 2),
            "expected_reward_usd": round(expected_reward_usd, 2),
            "primary_risks": primary_risks,
            "supporting_evidence": supporting_evidence,
            "alternative_outcomes": alternative_outcomes,
            "risk_reward_ratio": round(rr_ratio, 2)
        }
