from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from database import CognitiveBiasLog, Trade, JournalEntry, Signal, get_session

logger = logging.getLogger(__name__)


class CognitiveBiasService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None

    def get_logs_for_user(self, user_id: int) -> List[CognitiveBiasLog]:
        session = self.session_factory()
        try:
            return session.query(CognitiveBiasLog).filter(CognitiveBiasLog.user_id == user_id).all()
        finally:
            if not self.is_test:
                session.close()

    def detect_biases_for_trade(self, user_id: int, trade_id: int) -> List[CognitiveBiasLog]:
        session = self.session_factory()
        detected = []
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return []

            # 1. FOMO Detector
            # Triggered if entered price is > 3% above signal entry trigger, or with very quick entry
            signal = None
            if trade.signal_id:
                signal = session.query(Signal).filter(Signal.id == trade.signal_id).first()

            if signal and trade.entry and signal.price:
                price_pct_diff = ((trade.entry - signal.price) / signal.price) * 100.0 if signal.price > 0 else 0.0
                if trade.side == "LONG" and price_pct_diff > 3.0:
                    bias = CognitiveBiasLog(
                        user_id=user_id,
                        decision_id=trade.signal_id,
                        bias_type="FOMO",
                        confidence=0.9,
                        evidence={
                            "signal_price": signal.price,
                            "entry_price": trade.entry,
                            "pct_increase": round(price_pct_diff, 2)
                        },
                        explanation=f"You bought {trade.symbol} at {trade.entry}, which is {round(price_pct_diff, 1)}% higher than recommended signal price of {signal.price}.",
                        suggested_improvement="Consider using automated limit orders at recommended entry prices instead of chasing market pumps."
                    )
                    session.add(bias)
                    detected.append(bias)
                    logger.info("TELEMETRY: [Cognitive Bias] Detected FOMO on trade %s with confidence 0.9", trade_id)

            # 2. Revenge Trading Detector
            # Triggered if trade is opened within 15 mins of another trade closing as SL_HIT
            if trade.created_at:
                past_trades = (
                    session.query(Trade)
                    .filter(Trade.id != trade.id, Trade.closed_at.isnot(None))
                    .order_by(Trade.closed_at.desc())
                    .all()
                )
                for pt in past_trades:
                    if pt.status == "SL_HIT" and pt.closed_at:
                        time_diff_min = (trade.created_at - pt.closed_at).total_seconds() / 60.0
                        if 0 <= time_diff_min <= 15.0:
                            bias = CognitiveBiasLog(
                                user_id=user_id,
                                decision_id=trade.signal_id,
                                bias_type="REVENGE_TRADING",
                                confidence=0.85,
                                evidence={
                                    "previous_trade_id": pt.id,
                                    "previous_trade_status": pt.status,
                                    "time_since_last_loss_minutes": round(time_diff_min, 2)
                                },
                                explanation=f"Opened {trade.symbol} position within {round(time_diff_min, 1)} minutes of a stop-loss hit on trade #{pt.id}.",
                                suggested_improvement="Take a disciplined 30-minute break after any stop-loss event to prevent emotional, uncalibrated revenge trades."
                            )
                            session.add(bias)
                            detected.append(bias)
                            logger.info("TELEMETRY: [Cognitive Bias] Detected REVENGE_TRADING on trade %s with confidence 0.85", trade_id)
                            break

            # 3. Overconfidence Detector
            # Triggered if user entered a trade with very high confidence score but low system score
            if signal and signal.confidence and signal.score:
                if signal.confidence >= 90.0 and signal.score < 0.6:
                    bias = CognitiveBiasLog(
                        user_id=user_id,
                        decision_id=trade.signal_id,
                        bias_type="OVERCONFIDENCE",
                        confidence=0.8,
                        evidence={
                            "user_confidence": signal.confidence,
                            "system_score": signal.score
                        },
                        explanation="Decision confidence was set extremely high (>=90%) despite the system rating this signal with a low score (<60%).",
                        suggested_improvement="Calibrate your execution confidence strictly against evidence-based indicators and system scores."
                    )
                    session.add(bias)
                    detected.append(bias)
                    logger.info("TELEMETRY: [Cognitive Bias] Detected OVERCONFIDENCE on trade %s with confidence 0.8", trade_id)

            if not self.is_test:
                session.commit()
            else:
                session.flush()

            for b in detected:
                if not self.is_test:
                    session.refresh(b)
            return detected
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Error executing bias detection for trade %s: %s", trade_id, e)
            raise
        finally:
            if not self.is_test:
                session.close()
