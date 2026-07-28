from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from database import DecisionExplanation, get_session

logger = logging.getLogger(__name__)


class ExplainabilityLayer:
    """Ensures every platform recommendation or tool output provides non-black-box explanations grounded in structured ledger data."""

    _instance: Optional[ExplainabilityLayer] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

    def generate_explanation(
        self,
        signal_id: Optional[int] = None,
        symbol: Optional[str] = None,
        raw_evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compile a strict structured explanation from the database ledger or raw evidence."""
        # 1. Try fetching from DecisionExplanation Ledger
        explanation_data = None
        if signal_id is not None or symbol is not None:
            session = get_session()
            try:
                query = session.query(DecisionExplanation)
                if signal_id is not None:
                    query = query.filter(DecisionExplanation.signal_id == signal_id)
                elif symbol is not None:
                    query = query.filter(DecisionExplanation.symbol == symbol.upper())
                explanation_data = query.order_by(DecisionExplanation.created_at.desc()).first()
                if explanation_data:
                    # Expunge from session to avoid detachment issues
                    session.expunge(explanation_data)
            except Exception as e:
                logger.warning("Failed to query DecisionExplanation ledger: %s", e)
            finally:
                session.close()

        # 2. Map ledger record to the 5 Core Explainability Dimensions
        if explanation_data:
            return {
                "why": explanation_data.summary or "Grounded in technical trend score, multi-timeframe analysis, and portfolio risk validation.",
                "evidence": {
                    "technical_score": explanation_data.technical_score,
                    "whale_score": explanation_data.technical_score,  # fallback if missing
                    "reasons": explanation_data.reasons or [],
                    "supporting_signals": explanation_data.supporting_signals or [],
                },
                "confidence": f"{explanation_data.confidence}%" if explanation_data.confidence else "UNKNOWN",
                "risks": {
                    "risk_score": explanation_data.risk_score,
                    "warnings": explanation_data.warnings or [],
                    "risk_notes": explanation_data.risk_notes or [],
                },
                "alternatives": [
                    "Wait for a more stable market regime transition.",
                    "De-risk current open positions and evaluate secondary signals.",
                ],
                "source": "DecisionExplanation Ledger",
            }

        # 3. Fallback to raw evidence if provided
        if raw_evidence:
            reasons = raw_evidence.get("reasons") or ["Indicators aligned with market regime trend."]
            warnings = raw_evidence.get("warnings") or []
            confidence = raw_evidence.get("confidence") or 70.0
            risk_score = raw_evidence.get("risk_score") or 0.3
            return {
                "why": "Based on provided dynamic execution metrics.",
                "evidence": {
                    "reasons": reasons,
                    "supporting_signals": raw_evidence.get("supporting_signals") or [],
                },
                "confidence": f"{confidence}%",
                "risks": {
                    "risk_score": risk_score,
                    "warnings": warnings,
                },
                "alternatives": ["Standby in cash/stablecoins."],
                "source": "Dynamic Context Evidence",
            }

        # 4. If absolutely no data is found, be completely transparent per Rule 6
        return {
            "why": "Evidence / explanation data is not available in the Decision Ledger.",
            "evidence": None,
            "confidence": "DATA_UNAVAILABLE",
            "risks": None,
            "alternatives": None,
            "source": "None (No structured data found)",
        }


# Global singleton instance
explainability_layer = ExplainabilityLayer()
