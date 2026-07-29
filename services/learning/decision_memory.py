from __future__ import annotations

import logging
import math
from typing import Any, Callable, Optional, List, Dict

from database import DecisionMemory, Signal, Trade, DecisionExplanation, get_session

logger = logging.getLogger(__name__)


class DecisionMemoryService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def sync_memories(self) -> int:
        """
        Scan Signals, Trades, and DecisionExplanations, and sync them
        into the DecisionMemory table. Returns the number of synced records.
        """
        session = self.session_factory()
        synced_count = 0
        try:
            # Get all signals
            signals = session.query(Signal).all()
            for sig in signals:
                decision_id = f"DEC-{sig.id}"

                # Check if already exists
                existing = session.query(DecisionMemory).filter(DecisionMemory.decision_id == decision_id).first()

                # Find matching trade and explanation
                trade = session.query(Trade).filter(Trade.signal_id == sig.id).first()
                explanation = session.query(DecisionExplanation).filter(DecisionExplanation.signal_id == sig.id).first()

                dna = {
                    "trend_score": sig.trend_score or 0.0,
                    "volume_score": sig.volume_score or 0.0,
                    "btc_score": sig.btc_health or 0.0,
                    "mtf_score": (sig.trend_score + sig.volume_score + sig.btc_health) / 3.0 if (sig.trend_score and sig.volume_score and sig.btc_health) else 0.0,
                    "risk_score": sig.risk_score or 0.0,
                    "confidence": sig.confidence or 0.0,
                    "score": sig.score or 0.0,
                }

                context = {
                    "price": sig.price or 0.0,
                    "timeframe": sig.timeframe,
                    "divergence": sig.divergence,
                    "market_health": sig.market_health or 0.0,
                    "btc_health": sig.btc_health or 0.0,
                    "funding_score": sig.funding_score or 0.0,
                    "oi_score": sig.oi_score or 0.0,
                    "cvd_score": sig.cvd_score or 0.0,
                }

                reasoning = []
                if explanation:
                    reasoning = explanation.reasons or []
                    if explanation.summary:
                        reasoning.append(explanation.summary)
                elif sig.reason:
                    reasoning = [sig.reason]

                outcome = {}
                if trade:
                    outcome = {
                        "pnl": trade.pnl or 0.0,
                        "status": trade.status,
                        "result": "WIN" if (trade.pnl and trade.pnl > 0) else ("LOSS" if (trade.pnl and trade.pnl < 0) else "PENDING"),
                        "exit_price": trade.exit_price,
                        "close_reason": trade.close_reason,
                    }
                    if trade.closed_at and trade.created_at:
                        outcome["duration_seconds"] = (trade.closed_at - trade.created_at).total_seconds()

                if existing:
                    # Update dynamic outcome & context in case they changed
                    existing.outcome = outcome
                    existing.context = context
                    existing.decision_dna = dna
                    existing.reasoning_chain = reasoning
                else:
                    new_mem = DecisionMemory(
                        decision_id=decision_id,
                        signal_id=sig.id,
                        trade_id=trade.id if trade else None,
                        symbol=sig.symbol,
                        side=sig.side,
                        timeframe=sig.timeframe,
                        decision_dna=dna,
                        context=context,
                        reasoning_chain=reasoning,
                        outcome=outcome,
                    )
                    session.add(new_mem)
                    synced_count += 1

            session.commit()
            logger.info("Successfully synced %d decision memories", synced_count)
        except Exception as e:
            session.rollback()
            logger.error("Failed to sync decision memories: %s", e)
        finally:
            session.close()
        return synced_count

    def get_memories(
        self,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        result: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        session = self.session_factory()
        try:
            query = session.query(DecisionMemory)
            if symbol:
                query = query.filter(DecisionMemory.symbol == symbol.upper())
            if side:
                query = query.filter(DecisionMemory.side == side.upper())

            # Perform pagination
            all_memories = query.order_by(DecisionMemory.created_at.desc()).all()

            # Since outcome is a JSON column, we filter 'result' in memory for simplicity/robustness
            filtered = []
            for mem in all_memories:
                mem_dict = self._serialize_memory(mem)
                if result and mem_dict["outcome"].get("result") != result.upper():
                    continue
                filtered.append(mem_dict)

            return filtered[offset : offset + limit]
        finally:
            session.close()

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        session = self.session_factory()
        try:
            mem = session.query(DecisionMemory).filter(
                (DecisionMemory.decision_id == memory_id) | (DecisionMemory.id == memory_id)
            ).first()
            return self._serialize_memory(mem) if mem else None
        finally:
            session.close()

    def find_similar(self, memory_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search on Decision DNA scores using Cosine Similarity.
        """
        session = self.session_factory()
        try:
            target = session.query(DecisionMemory).filter(
                (DecisionMemory.decision_id == memory_id) | (DecisionMemory.id == memory_id)
            ).first()
            if not target:
                return []

            target_vector = self._get_dna_vector(target.decision_dna)

            all_memories = session.query(DecisionMemory).filter(DecisionMemory.id != target.id).all()
            similarities = []

            for mem in all_memories:
                vec = self._get_dna_vector(mem.decision_dna)
                sim = self._cosine_similarity(target_vector, vec)
                similarities.append((sim, mem))

            # Sort by similarity descending
            similarities.sort(key=lambda x: x[0], reverse=True)

            results = []
            for sim, mem in similarities[:limit]:
                serialized = self._serialize_memory(mem)
                serialized["similarity_score"] = round(sim, 4)
                results.append(serialized)

            return results
        finally:
            session.close()

    def _get_dna_vector(self, dna: Dict[str, Any]) -> List[float]:
        keys = ["trend_score", "volume_score", "btc_score", "mtf_score", "risk_score", "confidence", "score"]
        return [float(dna.get(k, 0.0)) for k in keys]

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 1.0 if vec_a == vec_b else 0.0

        return dot_product / (norm_a * norm_b)

    def _serialize_memory(self, mem: DecisionMemory) -> Dict[str, Any]:
        return {
            "id": mem.id,
            "decision_id": mem.decision_id,
            "signal_id": mem.signal_id,
            "trade_id": mem.trade_id,
            "symbol": mem.symbol,
            "side": mem.side,
            "timeframe": mem.timeframe,
            "decision_dna": mem.decision_dna,
            "context": mem.context,
            "reasoning_chain": mem.reasoning_chain,
            "outcome": mem.outcome,
            "created_at": mem.created_at.isoformat() if mem.created_at else None,
        }
