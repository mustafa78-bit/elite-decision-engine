from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from database import DecisionDNA, Trade, JournalEntry, Signal, get_session

logger = logging.getLogger(__name__)


class DecisionDNAService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None

    def get_or_create_profile(self, user_id: int) -> DecisionDNA:
        session = self.session_factory()
        try:
            profile = session.query(DecisionDNA).filter(DecisionDNA.user_id == user_id).first()
            if not profile:
                profile = DecisionDNA(
                    user_id=user_id,
                    risk_profile="MODERATE",
                    decision_speed_seconds=15.0,
                    average_holding_duration_seconds=86400.0,
                    preferred_market_regimes=["BULL", "SIDEWAYS"],
                    preferred_strategies=["EMA_CROSS", "BREAKOUT"],
                    win_loss_ratio=1.0,
                    confidence_calibration_score=0.0,
                    trading_discipline_score=100.0,
                    behavioral_tendencies={
                        "fomo_vulnerability": 0.1,
                        "loss_aversion_factor": 1.0,
                        "revenge_trading_propensity": 0.05
                    }
                )
                session.add(profile)
                if not self.is_test:
                    session.commit()
                    session.refresh(profile)
                else:
                    session.flush()
                logger.info("TELEMETRY: [DecisionDNA] Initialized new profile for user %s", user_id)
            else:
                logger.info("TELEMETRY: [DecisionDNA] Retrieved existing profile for user %s", user_id)
            return profile
        finally:
            if not self.is_test:
                session.close()

    def update_profile_from_history(self, user_id: int) -> DecisionDNA:
        session = self.session_factory()
        try:
            profile = session.query(DecisionDNA).filter(DecisionDNA.user_id == user_id).first()
            if not profile:
                profile = DecisionDNA(user_id=user_id)
                session.add(profile)
                if not self.is_test:
                    session.commit()
                    session.refresh(profile)
                else:
                    session.flush()

            # Analyze Trades
            trades = session.query(Trade).all() # Simplification for mock/test scoped DB
            closed_trades = [t for t in trades if t.status in ["CLOSED", "TP_HIT", "SL_HIT"]]

            wins = len([t for t in closed_trades if t.pnl and t.pnl > 0])
            losses = len([t for t in closed_trades if t.pnl and t.pnl <= 0])

            if losses > 0:
                profile.win_loss_ratio = round(wins / losses, 2)
            elif wins > 0:
                profile.win_loss_ratio = float(wins)
            else:
                profile.win_loss_ratio = 1.0

            # Durations
            durations = []
            for t in closed_trades:
                if t.closed_at and t.created_at:
                    diff = (t.closed_at - t.created_at).total_seconds()
                    durations.append(diff)
            if durations:
                profile.average_holding_duration_seconds = round(sum(durations) / len(durations), 1)

            # Signals to determine strategy preference
            signals = session.query(Signal).all()
            strategies = set()
            for s in signals:
                if s.divergence:
                    strategies.add(s.divergence.upper())
            if strategies:
                profile.preferred_strategies = list(strategies)

            # Discipline Score Calculation
            # Base 100, subtract penalties if there are failures
            discipline = 100.0
            if closed_trades:
                # Penalty if we hit SL_HIT
                sl_hits = len([t for t in closed_trades if t.status == "SL_HIT"])
                discipline -= sl_hits * 5.0
            profile.trading_discipline_score = max(50.0, discipline)

            if not self.is_test:
                session.commit()
                session.refresh(profile)
            else:
                session.flush()
            logger.info("TELEMETRY: [DecisionDNA] Rebuilt and calibrated profile for user %s from history", user_id)
            return profile
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to update DNA profile for user %s: %s", user_id, e)
            raise
        finally:
            if not self.is_test:
                session.close()
