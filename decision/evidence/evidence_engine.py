from __future__ import annotations

import logging
from typing import Any, Optional

from decision.evidence.dto import EvidenceReport
from decision.evidence.evidence_builder import EvidenceBuilder

logger = logging.getLogger(__name__)


class EvidenceEngine:
    def __init__(self) -> None:
        self._builder = EvidenceBuilder()
        self._reports: dict[str, EvidenceReport] = {}
        self._latest: Optional[EvidenceReport] = None

    def build(
        self,
        decision_result: Any = None,
        risk_result: Any = None,
        scanner_result: Any = None,
        council_result: Any = None,
        portfolio_result: Any = None,
        market_regime_result: Any = None,
        whale_result: Any = None,
        explain_result: Any = None,
        symbol: str = "",
        recommendation: str = "",
    ) -> EvidenceReport:
        report = self._builder.build(
            decision_result=decision_result,
            risk_result=risk_result,
            scanner_result=scanner_result,
            council_result=council_result,
            portfolio_result=portfolio_result,
            market_regime_result=market_regime_result,
            whale_result=whale_result,
            explain_result=explain_result,
            symbol=symbol,
            recommendation=recommendation,
        )
        self._reports[report.decision_id] = report
        self._latest = report
        logger.info(
            "Evidence report built | id=%s | rec=%s | confidence=%s | strength=%s | quality=%s",
            report.decision_id,
            report.recommendation,
            f"{report.decision_confidence:.1f}",
            f"{report.evidence_strength:.1f}",
            report.decision_quality,
        )
        return report

    def get(self, decision_id: str) -> Optional[EvidenceReport]:
        return self._reports.get(decision_id)

    def latest(self) -> Optional[EvidenceReport]:
        return self._latest

    def timeline(self, decision_id: str) -> list[dict[str, Any]]:
        report = self._reports.get(decision_id)
        if report is None:
            return []
        return [e.to_dict() for e in report.timeline]

    def status(self) -> dict[str, Any]:
        return {
            "reports_stored": len(self._reports),
            "latest_id": self._latest.decision_id if self._latest else None,
        }
