from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from database import CoachingRecommendation, DecisionDNA, CognitiveBiasLog, Trade, get_session
from services.dna_service import DecisionDNAService

logger = logging.getLogger(__name__)


class CoachingService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None
        self.dna_service = DecisionDNAService(session_factory=self.session_factory)

    def _to_dict(self, rec: CoachingRecommendation) -> dict[str, Any]:
        return {
            "id": rec.id,
            "user_id": rec.user_id,
            "category": rec.category,
            "feedback": rec.feedback,
            "related_bias_ids": rec.related_bias_ids or [],
            "related_trade_ids": rec.related_trade_ids or [],
            "suggested_action": rec.suggested_action,
            "dismissed": rec.dismissed,
        }

    def generate_recommendations(self, user_id: int) -> List[dict[str, Any]]:
        session = self.session_factory()
        recommendations = []
        try:
            # 1. Fetch DNA profile
            dna = self.dna_service.get_or_create_profile(user_id)

            # 2. Fetch bias logs
            biases = session.query(CognitiveBiasLog).filter(CognitiveBiasLog.user_id == user_id).all()
            bias_ids = [b.id for b in biases]

            # 3. Analyze patterns
            # Pattern A: FOMO Coaching
            fomo_logs = [b for b in biases if b.bias_type == "FOMO"]
            if len(fomo_logs) >= 1:
                rec = CoachingRecommendation(
                    user_id=user_id,
                    category="PATTERN_BREAK",
                    feedback=f"Our analysis detected {len(fomo_logs)} FOMO events where execution entry deviated significantly from recommended signal levels.",
                    related_bias_ids=[b.id for b in fomo_logs],
                    related_trade_ids=[],
                    suggested_action="Utilize strict limit orders instead of market executions on major breakout signals."
                )
                session.add(rec)
                recommendations.append(rec)

            # Pattern B: Discipline Strengthening
            if dna["trading_discipline_score"] < 90.0:
                rec = CoachingRecommendation(
                    user_id=user_id,
                    category="HABIT_STRENGTHENING",
                    feedback=f"Your overall discipline rating is sub-optimal ({round(dna['trading_discipline_score'], 1)}). Repeated manual override actions are eroding expectation margins.",
                    related_bias_ids=bias_ids,
                    related_trade_ids=[],
                    suggested_action="Refrain from manually closing open positions. Allow stop-loss or take-profit targets to be executed deterministically by the system."
                )
                session.add(rec)
                recommendations.append(rec)

            # Default generic habit coach if no other matches
            if not recommendations:
                rec = CoachingRecommendation(
                    user_id=user_id,
                    category="HABIT_STRENGTHENING",
                    feedback="Your trading behavior exhibits excellent baseline discipline. Continue following un-black-boxed recommendation models.",
                    related_bias_ids=[],
                    related_trade_ids=[],
                    suggested_action="Maintain current risk management parameters."
                )
                session.add(rec)
                recommendations.append(rec)

            if not self.is_test:
                session.commit()
            else:
                session.flush()

            for r in recommendations:
                if not self.is_test:
                    session.refresh(r)

            # Telemetry
            logger.info(
                "TELEMETRY: [Coaching] Generated %s coaching insights for user %s. Discipline: %s",
                len(recommendations), user_id, dna["trading_discipline_score"]
            )

            return [self._to_dict(r) for r in recommendations]
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to generate coaching insights for user %s: %s", user_id, e)
            raise
        finally:
            if not self.is_test:
                session.close()

    def get_recommendations(self, user_id: int) -> List[dict[str, Any]]:
        session = self.session_factory()
        try:
            recs = session.query(CoachingRecommendation).filter(
                CoachingRecommendation.user_id == user_id,
                CoachingRecommendation.dismissed == False
            ).all()
            if not recs:
                # Generate new ones and return them mapped
                return self.generate_recommendations(user_id)
            return [self._to_dict(r) for r in recs]
        finally:
            if not self.is_test:
                session.close()
