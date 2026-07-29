from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from services.dna_service import DecisionDNAService
from services.bias_service import CognitiveBiasService
from services.simulator_service import DecisionSimulatorService
from services.debate_service import AIDebateService
from services.market_memory_service import MarketMemoryService
from database import get_session

logger = logging.getLogger(__name__)


class StrategicIntelligenceService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None

        # Instantiate dependent services sharing the same session factory
        self.dna_service = DecisionDNAService(session_factory=self.session_factory)
        self.bias_service = CognitiveBiasService(session_factory=self.session_factory)
        self.simulator_service = DecisionSimulatorService(session_factory=self.session_factory)
        self.debate_service = AIDebateService(session_factory=self.session_factory)
        self.market_memory_service = MarketMemoryService(session_factory=self.session_factory)

    def generate_strategic_assessment(self, symbol: str, user_id: int = 1) -> dict[str, Any]:
        # 1. Retrieve DNA profile (Pydantic/dict mapped)
        dna = self.dna_service.get_or_create_profile(user_id)

        # 2. Retrieve recent bias events (Pydantic/dict mapped)
        biases = self.bias_service.get_logs_for_user(user_id)
        fomo_count = len([b for b in biases if b["bias_type"] == "FOMO"])

        # 3. Simulate hypothetical trade to estimate expected parameters
        sim = self.simulator_service.simulate_decision(
            symbol=symbol,
            side="LONG",
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            position_size=10000.0,
            user_id=user_id
        )

        # 4. Orchestrate AI Council debate
        debate = self.debate_service.run_debate(symbol=symbol, side="LONG", user_id=user_id)

        # 5. Integrate historical Market Memory matching current context/regime
        # Retrieve similar contexts matching current TREND regime as captured previously
        past_snaps = self.market_memory_service.get_similar_contexts("TREND", limit=3)

        # 6. Formulate strategic assessment
        strategic_score = 80.0
        recommendations = []

        if dna["risk_profile"] == "CONSERVATIVE":
            strategic_score -= 5.0
            recommendations.append("Conservative trading protocol active. Prioritize asset protection.")
        elif dna["risk_profile"] == "AGGRESSIVE":
            strategic_score += 5.0
            recommendations.append("Aggressive expansion mode. Leverage high-confidence breakouts.")

        if fomo_count > 0:
            strategic_score -= fomo_count * 2.0
            recommendations.append(f"FOMO warnings detected ({fomo_count}). Decrease execution speed to avoid chasing market tops.")

        if debate["consensus_score"] < 0.7:
            strategic_score -= 10.0
            recommendations.append("AI Council consensus is split. We recommend reducing position sizing on new entries by 50%.")
        else:
            recommendations.append("AI Council consensus is aligned. Proceed with standard capital allocation.")

        # Synthesize with Market Memory snaps count
        if len(past_snaps) > 0:
            strategic_score += 2.0
            recommendations.append(f"Market Memory indicates {len(past_snaps)} matching regime patterns. Confidence score calibrated upwards.")
        else:
            recommendations.append("Initial market memory observation phase. Align closely with immediate trend bounds.")

        strategic_score = max(10.0, min(100.0, strategic_score))

        # Telemetry
        logger.info(
            "TELEMETRY: [StrategicIntelligence] Generated long-term strategic assessment for user %s on %s. Score: %s",
            user_id, symbol, strategic_score
        )

        return {
            "symbol": symbol,
            "user_id": user_id,
            "strategic_score": round(strategic_score, 2),
            "recommendations": recommendations,
            "dna_risk_profile": dna["risk_profile"],
            "consensus_score": debate["consensus_score"],
            "expected_reward_usd": sim["expected_reward_usd"]
        }
