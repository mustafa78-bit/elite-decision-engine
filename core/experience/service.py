import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.experience.models import ExperienceSubstrate, InstinctState, ExperienceGraduation
from core.experience.policy import ExperiencePolicy, GraduationPolicy

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

        # Incrementally update the distilled Instinct State if outcome is realized
        if outcome is not None and realized_at is not None:
            InstinctStateService.update_instinct_incrementally(
                session, symbol, timeframe, outcome, timestamp, realized_at, state_snapshot
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

        # Incrementally evolve Instinct State without scanning the history database
        InstinctStateService.update_instinct_incrementally(
            session, exp.symbol, exp.timeframe, outcome, exp.timestamp, realized_at, exp.state_snapshot
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

    Synthesizes and evolves behavioral disposition vectors incrementally on the fly.
    """

    @staticmethod
    def update_instinct_incrementally(
        session: Session,
        symbol: str,
        timeframe: str,
        outcome: float,
        timestamp: datetime,
        realized_at: datetime,
        state_snapshot: Dict[str, Any],
    ) -> InstinctState:
        """Incrementally evolve the instinct state (O(1) production operation).

        Avoids full table scans or historical replays.
        """
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if realized_at.tzinfo is None:
            realized_at = realized_at.replace(tzinfo=timezone.utc)

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
            instinct = InstinctState(
                symbol=symbol,
                timeframe=timeframe,
                disposition_vector={
                    "courage": 0.5,
                    "defensiveness": 0.3,
                    "conviction": 0.5,
                    "adaptability": 0.5,
                },
                win_rate=0.0,
                profit_factor=1.0,
                total_trades=0,
                avg_pnl=0.0,
                vibe_score=0.0,
                gross_wins=0.0,
                gross_losses=0.0,
                win_count=0,
                loss_count=0,
                cumulative_pnl=0.0,
                recent_outcomes=[],
                unique_regimes_encountered=[],
            )
            session.add(instinct)

        # 1. Update basic counts & running statistics safely (ensure defaults on old rows)
        instinct.total_trades = (instinct.total_trades or 0) + 1
        instinct.cumulative_pnl = (instinct.cumulative_pnl or 0.0) + outcome
        instinct.avg_pnl = instinct.cumulative_pnl / instinct.total_trades

        if outcome > 0:
            instinct.win_count = (instinct.win_count or 0) + 1
            instinct.gross_wins = (instinct.gross_wins or 0.0) + outcome
        elif outcome < 0:
            instinct.loss_count = (instinct.loss_count or 0) + 1
            instinct.gross_losses = (instinct.gross_losses or 0.0) + abs(outcome)

        instinct.win_rate = (instinct.win_count or 0) / instinct.total_trades
        denom = instinct.gross_losses or 0.0
        instinct.profit_factor = (instinct.gross_wins or 0.0) / denom if denom > 0 else (instinct.gross_wins if (instinct.gross_wins or 0.0) > 0 else 1.0)

        # 2. Update recent outcomes (bounded queue)
        recent = list(instinct.recent_outcomes or [])
        recent.append(outcome)
        instinct.recent_outcomes = recent[-5:]

        # 3. Compute vibe score from recent outcomes
        weighted_sum = 0.0
        weight_total = 0.0
        for idx, out in enumerate(reversed(instinct.recent_outcomes)):
            weight = 1.0 / (idx + 1)
            sig = 1.0 if out > 0 else (-1.0 if out < 0 else 0.0)
            weighted_sum += sig * weight
            weight_total += weight
        instinct.vibe_score = weighted_sum / weight_total if weight_total > 0 else 0.0

        # 4. Evolve disposition vector incrementally based on current vector state
        disp = dict(instinct.disposition_vector or {
            "courage": 0.5,
            "defensiveness": 0.3,
            "conviction": 0.5,
            "adaptability": 0.5,
        })
        if outcome > 0:
            disp["defensiveness"] = max(0.1, disp["defensiveness"] - 0.1 * disp["defensiveness"])
            disp["conviction"] = min(0.95, disp["conviction"] + 0.1 * (1.0 - disp["conviction"]))
            disp["courage"] = min(0.9, disp["courage"] + 0.05 * (1.0 - disp["courage"]))
        else:
            disp["defensiveness"] = min(0.95, disp["defensiveness"] + 0.2 * (1.0 - disp["defensiveness"]))
            disp["conviction"] = max(0.1, disp["conviction"] - 0.15 * disp["conviction"])
            disp["courage"] = max(0.1, disp["courage"] - 0.1 * disp["courage"])

        regime = state_snapshot.get("regime", "UNKNOWN")
        if regime != "UNKNOWN" and outcome > 0:
            disp["adaptability"] = min(0.95, disp["adaptability"] + 0.03)

        instinct.disposition_vector = disp

        # 5. Chronological bounds & regimes (timezone-safe SQLite naive comparisons)
        ts_naive = timestamp.replace(tzinfo=None)

        if instinct.first_experience_time is None:
            instinct.first_experience_time = timestamp
        else:
            first_naive = instinct.first_experience_time.replace(tzinfo=None)
            if ts_naive < first_naive:
                instinct.first_experience_time = timestamp

        if instinct.last_experience_time is None:
            instinct.last_experience_time = timestamp
        else:
            last_naive = instinct.last_experience_time.replace(tzinfo=None)
            if ts_naive > last_naive:
                instinct.last_experience_time = timestamp

        regimes_list = list(instinct.unique_regimes_encountered or [])
        if regime != "UNKNOWN" and regime not in regimes_list:
            regimes_list.append(regime)
            instinct.unique_regimes_encountered = regimes_list

        session.commit()
        session.refresh(instinct)

        logger.info(
            "Incrementally Evolved Instinct for %s %s: total_trades=%s, win_rate=%.2f, vibe=%.2f, disposition=%s",
            symbol,
            timeframe,
            instinct.total_trades,
            instinct.win_rate,
            instinct.vibe_score,
            disp,
        )
        return instinct

    @staticmethod
    def compute_and_update_instinct(
        session: Session,
        symbol: str,
        timeframe: str,
        current_time: datetime,
    ) -> InstinctState:
        """Historical Replay / Reconstruction.

        Only used for rebuilding, migrations, recovery, or debugging.
        Ensures exact parity with the incremental builder.
        """
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Clear existing to rebuild correctly from scratch
        existing = (
            session.query(InstinctState)
            .filter(
                and_(
                    InstinctState.symbol == symbol,
                    InstinctState.timeframe == timeframe,
                )
            )
            .first()
        )
        if existing:
            session.delete(existing)
            session.commit()

        # Replay realized history chronologically
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

        inst_state = None
        for exp in realized_exps:
            inst_state = InstinctStateService.update_instinct_incrementally(
                session, symbol, timeframe, exp.outcome, exp.timestamp, exp.realized_at, exp.state_snapshot
            )

        if not inst_state:
            # Return fresh empty state if no history exists
            inst_state = InstinctState(
                symbol=symbol,
                timeframe=timeframe,
                disposition_vector={
                    "courage": 0.5,
                    "defensiveness": 0.3,
                    "conviction": 0.5,
                    "adaptability": 0.5,
                },
                win_rate=0.0,
                profit_factor=1.0,
                total_trades=0,
                avg_pnl=0.0,
                vibe_score=0.0,
                gross_wins=0.0,
                gross_losses=0.0,
                win_count=0,
                loss_count=0,
                cumulative_pnl=0.0,
                recent_outcomes=[],
                unique_regimes_encountered=[],
            )
            session.add(inst_state)
            session.commit()
            session.refresh(inst_state)

        return inst_state


class FamiliaritySignalService:
    """XI-3: Familiarity Signal Service.

    Calculates familiarity of current state by consulting the distilled Instinct State.
    Extensible design allowing multiple evaluating dimensions without rewriting the service.
    """

    # Extensible evaluator registries
    _dimension_evaluators: List[Callable[[Dict[str, Any], Dict[str, Any]], float]] = []

    @classmethod
    def register_evaluator(cls, evaluator: Callable[[Dict[str, Any], Dict[str, Any]], float]) -> None:
        """Register a new evaluation dimension dynamically."""
        cls._dimension_evaluators.append(evaluator)

    @classmethod
    def _evaluate_trend_direction(cls, current_feat: Dict[str, Any], distilled_metrics: Dict[str, Any]) -> float:
        """Evaluate similarity of current trend vs historical vibe direction."""
        trend_score = float(current_feat.get("trend_score", 0.5))
        vibe = distilled_metrics.get("vibe_score", 0.0)
        vibe_direction = 1.0 if vibe >= 0 else 0.0
        trend_direction = 1.0 if trend_score > 0.5 else 0.0
        return 1.0 if vibe_direction == trend_direction else 0.4

    @staticmethod
    def calculate_familiarity(
        session: Session,
        symbol: str,
        timeframe: str,
        current_features: Dict[str, Any],
        current_time: datetime,
    ) -> float:
        """Calculate familiarity by analyzing how well the current features match distilled Instinct State.

        Avoids full database scans in normal operations.
        """
        if current_time.tzinfo is None:
            current_time = current_time.replace(timezone.utc)

        # Consult distilled Instinct State
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

        disp = instinct.disposition_vector
        conviction = disp.get("conviction", 0.5)
        defensiveness = disp.get("defensiveness", 0.3)

        # Base evaluations
        dist_metrics = {"vibe_score": instinct.vibe_score}
        direction_match = FamiliaritySignalService._evaluate_trend_direction(current_features, dist_metrics)

        # Composite score
        base_fam = conviction * direction_match * (1.0 - abs(defensiveness - 0.5) * 0.5)

        # Extensible Evaluations: evaluate any registered dimensions
        extra_evals = []
        for eval_func in FamiliaritySignalService._dimension_evaluators:
            try:
                extra_evals.append(eval_func(current_features, {
                    "disposition": disp,
                    "vibe_score": instinct.vibe_score,
                    "unique_regimes": instinct.unique_regimes_encountered,
                }))
            except Exception as e:
                logger.warning("Familiarity evaluator dimension failed: %s", e)

        if extra_evals:
            # Blended composite
            composite = (base_fam + sum(extra_evals)) / (1 + len(extra_evals))
        else:
            composite = base_fam

        fam_score = max(0.0, min(1.0, composite))
        logger.info(
            "Familiarity calculated from distilled Instinct for %s %s: %.4f",
            symbol,
            timeframe,
            fam_score,
        )
        return fam_score


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
        """Contrast independent dimensions: Knowledge vs Experience.

        Uses pre-computed state to prevent slow db scans.
        """
        if current_time.tzinfo is None:
            current_time = current_time.replace(timezone.utc)

        # Consult distilled state
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

        experience_score = 0.5
        vibe = 0.0
        total_trades = 0
        if instinct:
            experience_score = instinct.win_rate
            vibe = instinct.vibe_score
            total_trades = instinct.total_trades

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
                "vibe": round(vibe, 4),
                "total_lived_trades": total_trades,
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
    Reads distilled state to avoid SQL table scans.
    """

    @staticmethod
    def check_sufficiency(
        session: Session,
        symbol: str,
        timeframe: str,
        current_time: datetime,
    ) -> Dict[str, Any]:
        """Evaluate if chronological experience is sufficient. Consults pre-distilled InstinctState."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(timezone.utc)

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

        count = 0
        duration_hours = 0.0
        regimes_encountered = []

        if instinct:
            count = instinct.total_trades
            regimes_encountered = list(instinct.unique_regimes_encountered or [])
            if instinct.first_experience_time:
                first_time = instinct.first_experience_time
                if first_time.tzinfo is None:
                    first_time = first_time.replace(tzinfo=timezone.utc)
                duration_hours = (current_time - first_time).total_seconds() / 3600.0

        # Governance Managed Thresholds
        min_events = ExperiencePolicy.get_min_events()
        min_hours = ExperiencePolicy.get_min_hours()

        missing_reasons = []
        if count < min_events:
            missing_reasons.append(f"Insufficient events ({count}/{min_events})")
        if duration_hours < min_hours:
            missing_reasons.append(f"Insufficient duration ({duration_hours:.1f}/{min_hours} hours)")

        is_sufficient = (count >= min_events) and (duration_hours >= min_hours)

        ratio_events = min(1.0, count / min_events) if min_events > 0 else 1.0
        ratio_duration = min(1.0, duration_hours / min_hours) if min_hours > 0 else 1.0
        sufficiency_ratio = (ratio_events + ratio_duration) / 2.0

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "is_sufficient": is_sufficient,
            "sufficiency_ratio": round(sufficiency_ratio, 4),
            "total_events": count,
            "duration_hours": round(duration_hours, 2),
            "regimes_encountered": regimes_encountered,
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
            current_time = current_time.replace(timezone.utc)

        # Evaluate sufficiency and instinct
        suff = ExperienceSufficiencyService.check_sufficiency(session, symbol, timeframe, current_time)
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

        is_sufficient = suff["is_sufficient"]
        recommend = False

        if instinct:
            # Governance-Managed Thresholds
            win_rate_threshold = GraduationPolicy.get_win_rate()
            pf_threshold = GraduationPolicy.get_profit_factor()
            min_trades_threshold = GraduationPolicy.get_min_trades()

            is_profitable = instinct.win_rate >= win_rate_threshold and instinct.profit_factor >= pf_threshold
            recommend = is_sufficient and is_profitable and instinct.total_trades >= min_trades_threshold

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
