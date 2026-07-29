from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from database import MarketRegimeSnap, get_session
from scoring.regime_ai import get_regime_ai

logger = logging.getLogger(__name__)


class MarketMemoryService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None
        self.regime_ai = get_regime_ai()

    def _to_dict(self, snap: MarketRegimeSnap) -> dict[str, Any]:
        return {
            "id": snap.id,
            "timestamp": snap.timestamp.isoformat() if snap.timestamp else None,
            "symbol": snap.symbol,
            "regime_type": snap.regime_type,
            "volatility_metric": snap.volatility_metric,
            "rsi_14": snap.rsi_14,
            "funding_rate": snap.funding_rate
        }

    def record_regime_snapshot(
        self,
        symbol: str,
        price: float,
        ema20: float,
        ema50: float,
        ema200: float,
        atr: float,
        rsi: float,
        funding_rate: float = 0.0,
    ) -> dict[str, Any]:
        session = self.session_factory()
        try:
            # 1. Classify regime using existing RegimeAI
            classification = self.regime_ai.detect({
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "atr": atr,
                "close": price,
                "rsi": rsi,
            })

            snap = MarketRegimeSnap(
                symbol=symbol,
                regime_type=classification.get("regime", "UNKNOWN"),
                volatility_metric=atr,
                rsi_14=rsi,
                funding_rate=funding_rate
            )

            session.add(snap)
            if not self.is_test:
                session.commit()
                session.refresh(snap)
            else:
                session.flush()

            # Telemetry
            logger.info(
                "TELEMETRY: [MarketMemory] Captured market regime snapshot for %s: %s (RSI: %s)",
                symbol, snap.regime_type, rsi
            )

            return self._to_dict(snap)
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to record market regime snapshot: %s", e)
            raise
        finally:
            if not self.is_test:
                session.close()

    def get_similar_contexts(self, regime_type: str, limit: int = 5) -> List[dict[str, Any]]:
        session = self.session_factory()
        try:
            snaps = (
                session.query(MarketRegimeSnap)
                .filter(MarketRegimeSnap.regime_type == regime_type)
                .order_by(MarketRegimeSnap.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(s) for s in snaps]
        finally:
            if not self.is_test:
                session.close()
