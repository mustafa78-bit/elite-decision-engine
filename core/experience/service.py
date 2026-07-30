import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.experience.models import ExperienceSubstrate, InstinctState, ExperienceGraduation

logger = logging.getLogger(__name__)


class ExperienceSubstrateService:
    """XI-1: Experience Substrate Service.

    Manages raw, chronological, walk-forward experience recording and querying.
    Ensures absolute blind historical progression with zero hindsight.
    """

    @staticmethod
    def record_experience(
        session: Session,
        timestamp: datetime,
        symbol: str,
        timeframe: str,
        state_snapshot: Dict[str, Any],
        action_taken: str,
        outcome: Optional[float] = None,
        realized_at: Optional[datetime] = None,
    ) -> ExperienceSubstrate:
        """Record a raw chronological experience. Earned only through chronological living."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if realized_at and realized_at.tzinfo is None:
            realized_at = realized_at.replace(tzinfo=timezone.utc)

        experience = ExperienceSubstrate(
            timestamp=timestamp,
            symbol=symbol,
            timeframe=timeframe,
            state_snapshot=state_snapshot,
            action_taken=action_taken,
            outcome=outcome,
            realized_at=realized_at,
        )
        session.add(experience)
        session.commit()
        session.refresh(experience)
        logger.info(
            "Recorded ExperienceSubstrate: %s %s at %s, action=%s",
            symbol,
            timeframe,
            timestamp,
            action_taken,
        )
        return experience

    @staticmethod
    def realize_experience(
        session: Session,
        substrate_id: int,
        outcome: float,
        realized_at: datetime,
    ) -> bool:
        """Realize an experience chronologically when its outcome becomes known."""
        if realized_at.tzinfo is None:
            realized_at = realized_at.replace(tzinfo=timezone.utc)

        exp = session.query(ExperienceSubstrate).filter(ExperienceSubstrate.id == substrate_id).first()
        if not exp:
            logger.warning("ExperienceSubstrate ID %s not found to realize", substrate_id)
            return False

        exp.outcome = outcome
        exp.realized_at = realized_at
        session.commit()
        logger.info(
            "Realized ExperienceSubstrate ID %s with outcome %s at %s",
            substrate_id,
            outcome,
            realized_at,
        )
        return True

    @staticmethod
    def get_historical_substrate(
        session: Session,
        current_time: datetime,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> List[ExperienceSubstrate]:
        """Strict walk-forward lookup: only returns experiences that occurred on or before current_time."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        query = session.query(ExperienceSubstrate).filter(ExperienceSubstrate.timestamp <= current_time)
        if symbol:
            query = query.filter(ExperienceSubstrate.symbol == symbol)
        if timeframe:
            query = query.filter(ExperienceSubstrate.timeframe == timeframe)

        return query.order_by(ExperienceSubstrate.timestamp.asc()).all()


class InstinctStateService:
    """XI-2: Instinct State Service.

    Synthesizes and evolves behavioral disposition vectors from chronological experiences.
    """

    @staticmethod
    def compute_and_update_instinct(
        session: Session,
        symbol: str,
        timeframe: str,
        current_time: datetime,
    ) -> InstinctState:
        """Compute Instinct state with continuously evolving disposition parameters up to current_time."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Query all realized experiences up to current_time
        realized_exps = (
            session.query(ExperienceSubstrate)
            .filter(
                and_(
                    ExperienceSubstrate.symbol == symbol,
                    ExperienceSubstrate.timeframe == timeframe,
                    ExperienceSubstrate.realized_at <= current_time,
                    ExperienceSubstrate.outcome.isnot(None),
                )
            )
            .order_by(ExperienceSubstrate.realized_at.asc())
            .all()
        )

        total_trades = len(realized_exps)

        # Evolving Instinctual Disposition Vectors:
        # courageousness: willingness to counter common rules
        # defensiveness: aversion to active risk
        # conviction: situational certainty
        # adaptability: responsiveness to regime transitions
        disposition = {
            "courage": 0.5,
            "defensiveness": 0.3,
            "conviction": 0.5,
            "adaptability": 0.5,
        }

        win_rate = 0.0
        profit_factor = 1.0
        avg_pnl = 0.0
        vibe_score = 0.0

        if total_trades > 0:
            wins = [e.outcome for e in realized_exps if e.outcome > 0]
            losses = [e.outcome for e in realized_exps if e.outcome < 0]

            win_rate = len(wins) / total_trades
            avg_pnl = sum(e.outcome for e in realized_exps) / total_trades

            gross_wins = sum(wins)
            gross_losses = abs(sum(losses))
            profit_factor = gross_wins / gross_losses if gross_losses > 0 else (gross_wins if gross_wins > 0 else 1.0)

            # Evolve disposition chronologically in a non-commutative, state-dependent manner
            for exp in realized_exps:
                pnl = exp.outcome
                # If winning, defensiveness goes down, conviction goes up
                if pnl > 0:
                    disposition["defensiveness"] = max(0.1, disposition["defensiveness"] - 0.1 * disposition["defensiveness"])
                    disposition["conviction"] = min(0.95, disposition["conviction"] + 0.1 * (1.0 - disposition["conviction"]))
                    disposition["courage"] = min(0.9, disposition["courage"] + 0.05 * (1.0 - disposition["courage"]))
                # If losing, defensiveness spikes, courage decays
                else:
                    disposition["defensiveness"] = min(0.95, disposition["defensiveness"] + 0.2 * (1.0 - disposition["defensiveness"]))
                    disposition["conviction"] = max(0.1, disposition["conviction"] - 0.15 * disposition["conviction"])
                    disposition["courage"] = max(0.1, disposition["courage"] - 0.1 * disposition["courage"])

                # Adaptability is influenced by regime transitions
                regime = exp.state_snapshot.get("regime", "UNKNOWN")
                if regime != "UNKNOWN" and pnl > 0:
                    disposition["adaptability"] = min(0.95, disposition["adaptability"] + 0.03)

            # Rolling vibe score: exponentially weighted average of recent outcomes
            recent_exps = realized_exps[-5:]
            weighted_sum = 0.0
            weight_total = 0.0
            for idx, exp in enumerate(reversed(recent_exps)):
                weight = 1.0 / (idx + 1)
                sig = 1.0 if exp.outcome > 0 else (-1.0 if exp.outcome < 0 else 0.0)
                weighted_sum += sig * weight
                weight_total += weight
            vibe_score = weighted_sum / weight_total if weight_total > 0 else 0.0

        instinct = (
            session.query(InstinctState)
            .filter(
                and_(
                    InstinctState.symbol == symbol,
                    InstinctState.timeframe == timeframe,
                )
            )
            .first()
        )

        if not instinct:
            instinct = InstinctState(symbol=symbol, timeframe=timeframe)
            session.add(instinct)

        instinct.disposition_vector = disposition
        instinct.win_rate = win_rate
        instinct.profit_factor = profit_factor
        instinct.total_trades = total_trades
        instinct.avg_pnl = avg_pnl
        instinct.vibe_score = vibe_score
        session.commit()
        session.refresh(instinct)

        logger.info(
            "Evolved Instinct for %s %s: total_trades=%s, win_rate=%.2f, vibe=%.2f, disposition=%s",
            symbol,
            timeframe,
            total_trades,
            win_rate,
            vibe_score,
            disposition,
        )
        return instinct


class FamiliaritySignalService:
    """XI-3: Familiarity Signal Service.

    Calculates familiarity of current state by consulting the distilled Instinct State.
    Does NOT query raw experienced substrates repeatedly (avoiding retrieval engines).
    """

    @staticmethod
    def calculate_familiarity(
        session: Session,
        symbol: str,
        timeframe: str,
        current_features: Dict[str, Any],
        current_time: datetime,
    ) -> float:
        """Calculate familiarity by analyzing how well the current features match distilled Instinct State."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(timezone.utc)

        # Consult pre-computed distilled Instinct State
        instinct = (
            session.query(InstinctState)
            .filter(
                and_(
                    InstinctState.symbol == symbol,
                    InstinctState.timeframe == timeframe,
                )
            )
            .first()
        )

        if not instinct or instinct.total_trades == 0:
            logger.debug("No instinct state compiled yet for %s %s", symbol, timeframe)
            return 0.0

        # We evaluate familiarity directly against the distilled disposition and status:
        # High conviction and moderate defensiveness represents a familiar state of stable living.
        disp = instinct.disposition_vector
        conviction = disp.get("conviction", 0.5)
        defensiveness = disp.get("defensiveness", 0.3)
        vibe = instinct.vibe_score

        # We compare features against the vibe. If current trend score matches the vibe direction, familiarity is higher.
        trend_score = float(current_features.get("trend_score", 0.5))
        vibe_direction = 1.0 if vibe >= 0 else 0.0
        trend_direction = 1.0 if trend_score > 0.5 else 0.0

        direction_match = 1.0 if vibe_direction == trend_direction else 0.4

        # Compute familiarity signal purely from distilled instinct metrics without DB search
        familiarity = conviction * direction_match * (1.0 - abs(defensiveness - 0.5) * 0.5)
        familiarity = max(0.0, min(1.0, familiarity))

        logger.info(
            "Familiarity calculated from distilled Instinct for %s %s: %.4f",
            symbol,
            timeframe,
            familiarity,
        )
        return familiarity


class ExperienceVsKnowledgeService:
    """XI-4: Experience vs Knowledge Service.

    Contrasts pre-trained rules (Knowledge: What should happen?) vs Lived Experience (What has actually happened?).
    Dimensions remain independent. Do NOT blend/merge into a single score.
    """

    @staticmethod
    def contrast_experience_vs_knowledge(
        session: Session,
        symbol: str,
        timeframe: str,
        current_features: Dict[str, Any],
        knowledge_score: float,
        current_time: datetime,
    ) -> Dict[str, Any]:
        """Contrast independent dimensions: Knowledge vs Experience."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(timezone.utc)

        # 1. Knowledge dimension (What should happen?)
        # Represented by knowledge_score from original pre-trained rules / filters

        # 2. Experience dimension (What has actually happened during my lived history?)
        # Consult instinct state up to current_time
        instinct = InstinctStateService.compute_and_update_instinct(
            session, symbol, timeframe, current_time
        )

        # Experience score based strictly on actual historical win-rate and disposition vector
        experience_score = instinct.win_rate if instinct.total_trades > 0 else 0.5

        # Compute alignment/divergence between the two independent dimensions
        divergence = abs(knowledge_score - experience_score)
        alignment = 1.0 - divergence

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "knowledge_dimension": {
                "label": "Knowledge: What should happen?",
                "score": round(knowledge_score, 4),
            },
            "experience_dimension": {
                "label": "Experience: What has actually happened in my history?",
                "score": round(experience_score, 4),
                "vibe": round(instinct.vibe_score, 4),
                "total_lived_trades": instinct.total_trades,
            },
            "divergence": round(divergence, 4),
            "alignment": round(alignment, 4),
        }
        logger.info(
            "Independent Contrast for %s %s: Knowledge=%.2f, Experience=%.2f, Divergence=%.2f",
            symbol,
            timeframe,
            knowledge_score,
            experience_score,
            divergence,
        )
        return result


class ExperienceSufficiencyService:
    """XI-5: Experience Sufficiency Service.

    Evaluates if chronological experience is sufficient based on duration and event frequency.
    """

    @staticmethod
    def check_sufficiency(
        session: Session,
        symbol: str,
        timeframe: str,
        current_time: datetime,
    ) -> Dict[str, Any]:
        """Evaluate if chronological experience for the given environment is sufficient."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Query all experiences up to current_time
        exps = (
            session.query(ExperienceSubstrate)
            .filter(
                and_(
                    ExperienceSubstrate.symbol == symbol,
                    ExperienceSubstrate.timeframe == timeframe,
                    ExperienceSubstrate.timestamp <= current_time,
                )
            )
            .all()
        )

        count = len(exps)
        duration_hours = 0.0
        regimes_encountered = set()

        if count > 0:
            first_exp_time = min(e.timestamp for e in exps)
            if first_exp_time.tzinfo is None:
                first_exp_time = first_exp_time.replace(tzinfo=timezone.utc)
            duration_hours = (current_time - first_exp_time).total_seconds() / 3600.0

            for e in exps:
                regime = e.state_snapshot.get("regime")
                if regime:
                    regimes_encountered.add(regime)

        # Thresholds
        MIN_EVENTS = 5
        MIN_HOURS = 24

        missing_reasons = []
        if count < MIN_EVENTS:
            missing_reasons.append(f"Insufficient events ({count}/{MIN_EVENTS})")
        if duration_hours < MIN_HOURS:
            missing_reasons.append(f"Insufficient duration ({duration_hours:.1f}/{MIN_HOURS} hours)")

        is_sufficient = (count >= MIN_EVENTS) and (duration_hours >= MIN_HOURS)

        ratio_events = min(1.0, count / MIN_EVENTS)
        ratio_duration = min(1.0, duration_hours / MIN_HOURS)
        sufficiency_ratio = (ratio_events + ratio_duration) / 2.0

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "is_sufficient": is_sufficient,
            "sufficiency_ratio": round(sufficiency_ratio, 4),
            "total_events": count,
            "duration_hours": round(duration_hours, 2),
            "regimes_encountered": list(regimes_encountered),
            "missing_reasons": missing_reasons,
        }


class ExperienceGraduationService:
    """XI-6: Graduation & Governance Service.

    Evaluates and recommends promotion, but NEVER self-promotes.
    Promotion and active rule application require explicit Governance approval.
    """

    @staticmethod
    def evaluate_graduation_recommendation(
        session: Session,
        symbol: str,
        timeframe: str,
        current_time: datetime,
    ) -> ExperienceGraduation:
        """Recommend graduation based on performance, but does NOT activate promotion automatically."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Evaluate sufficiency and instinct
        suff = ExperienceSufficiencyService.check_sufficiency(session, symbol, timeframe, current_time)
        instinct = InstinctStateService.compute_and_update_instinct(session, symbol, timeframe, current_time)

        is_sufficient = suff["is_sufficient"]
        is_profitable = instinct.win_rate >= 0.55 and instinct.profit_factor >= 1.2

        recommend = is_sufficient and is_profitable and instinct.total_trades >= 5

        grad = (
            session.query(ExperienceGraduation)
            .filter(
                and_(
                    ExperienceGraduation.symbol == symbol,
                    ExperienceGraduation.timeframe == timeframe,
                )
            )
            .first()
        )

        if not grad:
            grad = ExperienceGraduation(symbol=symbol, timeframe=timeframe)
            session.add(grad)

        # Generate recommendation payload but DO NOT self-promote (keep status PENDING or RECOMMENDED)
        if recommend:
            if grad.status not in ["APPROVED_BY_GOVERNANCE", "REJECTED_BY_GOVERNANCE"]:
                grad.status = "RECOMMENDED"
                grad.recommended_at = current_time
            grad.recommendation_payload = {
                "position_size_multiplier": 1.25,
                "risk_limit_multiplier": 1.2,
                "max_open_trades_override": 5,
                "reason": "Sufficient chronological living with strong win_rate and profit_factor",
            }
        else:
            if grad.status not in ["APPROVED_BY_GOVERNANCE", "REJECTED_BY_GOVERNANCE"]:
                grad.status = "PENDING"
            grad.recommendation_payload = {}

        session.commit()
        session.refresh(grad)
        logger.info(
            "Graduation evaluated: symbol=%s, status=%s, graduated=%s (Requires Governance Approval)",
            symbol,
            grad.status,
            grad.graduated,
        )
        return grad

    @staticmethod
    def approve_graduation(
        session: Session,
        symbol: str,
        timeframe: str,
        governor_name: str,
        current_time: datetime,
    ) -> ExperienceGraduation:
        """Explicit Governance action: Approves and activates graduation rules."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(timezone.utc)

        grad = (
            session.query(ExperienceGraduation)
            .filter(
                and_(
                    ExperienceGraduation.symbol == symbol,
                    ExperienceGraduation.timeframe == timeframe,
                )
            )
            .first()
        )

        if not grad:
            grad = ExperienceGraduation(symbol=symbol, timeframe=timeframe)
            session.add(grad)

        # Force promotion explicitly through Governance
        grad.status = "APPROVED_BY_GOVERNANCE"
        grad.graduated = True
        grad.graduated_at = current_time

        # Retrieve proposed rules or apply defaults
        rules = grad.recommendation_payload or {
            "position_size_multiplier": 1.25,
            "risk_limit_multiplier": 1.2,
            "max_open_trades_override": 5,
        }
        grad.governance_rules = {
            **rules,
            "approved_by": governor_name,
            "approval_timestamp": current_time.isoformat(),
        }

        session.commit()
        session.refresh(grad)
        logger.info(
            "Governance APPROVED graduation for %s %s by %s. Rules activated: %s",
            symbol,
            timeframe,
            governor_name,
            grad.governance_rules,
        )
        return grad

    @staticmethod
    def reject_graduation(
        session: Session,
        symbol: str,
        timeframe: str,
        governor_name: str,
        current_time: datetime,
    ) -> ExperienceGraduation:
        """Explicit Governance action: Rejects or revokes graduation rules."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(timezone.utc)

        grad = (
            session.query(ExperienceGraduation)
            .filter(
                and_(
                    ExperienceGraduation.symbol == symbol,
                    ExperienceGraduation.timeframe == timeframe,
                )
            )
            .first()
        )

        if not grad:
            grad = ExperienceGraduation(symbol=symbol, timeframe=timeframe)
            session.add(grad)

        grad.status = "REJECTED_BY_GOVERNANCE"
        grad.graduated = False
        grad.graduated_at = None
        grad.governance_rules = {
            "position_size_multiplier": 1.0,
            "risk_limit_multiplier": 1.0,
            "rejected_by": governor_name,
            "rejection_timestamp": current_time.isoformat(),
        }

        session.commit()
        session.refresh(grad)
        logger.info(
            "Governance REJECTED graduation for %s %s by %s",
            symbol,
            timeframe,
            governor_name,
        )
        return grad
