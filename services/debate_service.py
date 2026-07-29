from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from services.dna_service import DecisionDNAService
from database import get_session

logger = logging.getLogger(__name__)


class AIDebateService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.dna_service = DecisionDNAService(session_factory=self.session_factory)

    def run_debate(
        self,
        symbol: str,
        side: str,
        user_id: int = 1,
    ) -> dict[str, Any]:
        # Consume Decision DNA
        dna = self.dna_service.get_or_create_profile(user_id)

        # Base consensus score
        consensus_score = 0.75
        minority_opinion = ""

        # Simulated structured arguments
        arguments = [
            f"Bull Analyst: Strong market regime support on {symbol}.",
            "Portfolio Manager: Cash balance supports additional allocation."
        ]
        counterarguments = [
            "Bear Analyst: Market is approaching major psychological resistance.",
            "Risk Officer: Funding rate volatility suggests warning."
        ]

        if dna.risk_profile == "CONSERVATIVE":
            consensus_score = 0.60
            minority_opinion = "Risk Officer strongly argues to scale down position due to conservative user profile."
        elif dna.risk_profile == "AGGRESSIVE":
            consensus_score = 0.85
            minority_opinion = "Bear Analyst raises minor concern on volume exhaustion."

        final_recommendation = "APPROVE" if consensus_score >= 0.70 else "APPROVE_HALF_SIZE"

        # Structured Telemetry
        logger.info(
            "TELEMETRY: [AIDebate] Orchestrated AI Council debate for %s. Consensus: %s. Recommendation: %s",
            symbol, consensus_score, final_recommendation
        )

        return {
            "symbol": symbol,
            "consensus_score": round(consensus_score, 2),
            "arguments": arguments,
            "counterarguments": counterarguments,
            "minority_opinion": minority_opinion,
            "final_recommendation": final_recommendation
        }
