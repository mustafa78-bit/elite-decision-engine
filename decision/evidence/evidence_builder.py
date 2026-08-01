from __future__ import annotations

from typing import Any, Optional

from decision.evidence.confidence import (
    calculate_confidence,
    calculate_decision_quality,
    calculate_evidence_strength,
    calculate_explainability,
)
from decision.evidence.conflict_detector import detect_conflicts
from decision.evidence.dto import EvidenceItem, EvidenceReport
from decision.evidence.parser import (
    parse_council_report,
    parse_decision_result,
    parse_explain_result,
    parse_market_regime,
    parse_portfolio_summary,
    parse_risk_decision,
    parse_scanner_opportunity,
    parse_whale_result,
)
from decision.evidence.source_trace import SourceTrace
from decision.evidence.timeline import build_timeline


class EvidenceBuilder:
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
        all_items: list[EvidenceItem] = []
        supporting: list[EvidenceItem] = []
        contradicting: list[EvidenceItem] = []
        all_warnings: list[str] = []
        all_risk_notes: list[str] = []
        all_sources: dict[str, SourceTrace] = {}

        if decision_result is not None:
            items = parse_decision_result(decision_result, symbol)
            all_items.extend(items)

        if risk_result is not None:
            items = parse_risk_decision(risk_result, symbol)
            all_items.extend(items)

        if scanner_result is not None:
            items = parse_scanner_opportunity(scanner_result)
            all_items.extend(items)

        if council_result is not None:
            items = parse_council_report(council_result)
            all_items.extend(items)

        if portfolio_result is not None:
            items = parse_portfolio_summary(portfolio_result)
            all_items.extend(items)

        if market_regime_result is not None:
            items = parse_market_regime(market_regime_result)
            all_items.extend(items)

        if whale_result is not None:
            items = parse_whale_result(whale_result)
            all_items.extend(items)

        if explain_result is not None:
            items = parse_explain_result(explain_result)
            all_items.extend(items)

        for item in all_items:
            if item.supports_decision:
                supporting.append(item)
            else:
                contradicting.append(item)
            if item.source:
                key = f"{item.source.engine}:{item.source.origin}"
                all_sources[key] = item.source

        decision_confidence = calculate_confidence(supporting, contradicting)
        evidence_strength = calculate_evidence_strength(supporting)
        timeline = build_timeline(all_items)
        explainability = calculate_explainability(supporting, contradicting, list(all_sources.values()), len(timeline))
        quality = calculate_decision_quality(
            decision_confidence, evidence_strength, explainability,
            len(supporting), len(contradicting),
        )

        conflicts = detect_conflicts(supporting, contradicting)

        reasoning = self._build_reasoning(supporting, contradicting, decision_confidence, evidence_strength, explainability, conflicts)
        summary = self._build_summary(recommendation, decision_confidence, evidence_strength, explainability, quality, supporting, contradicting)

        for item in contradicting:
            if "risk" in item.engine.lower() or "volatility" in item.category.lower():
                all_risk_notes.append(f"{item.title}: {item.description}")
            else:
                all_warnings.append(f"{item.title}: {item.description}")

        return EvidenceReport(
            recommendation=recommendation,
            decision_confidence=decision_confidence,
            evidence_strength=evidence_strength,
            explainability=explainability,
            decision_quality=quality,
            summary=summary,
            reasoning=reasoning,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            warnings=all_warnings,
            risk_notes=all_risk_notes,
            timeline=timeline,
            sources=list(all_sources.values()),
        )

    def _build_reasoning(
        self,
        supporting: list[EvidenceItem],
        contradicting: list[EvidenceItem],
        decision_confidence: float,
        evidence_strength: float,
        explainability: float,
        conflicts: list[Any],
    ) -> list[str]:
        lines: list[str] = []
        if supporting:
            lines.append(f"{len(supporting)} supporting evidence items.")
        if contradicting:
            lines.append(f"{len(contradicting)} contradicting evidence items.")
        lines.append(f"Decision confidence: {decision_confidence:.1f}%")
        lines.append(f"Evidence strength: {evidence_strength:.1f}%")
        lines.append(f"Explainability: {explainability:.1f}%")
        for item in supporting[:3]:
            lines.append(f"  + {item.title}: {item.description}")
        for item in contradicting[:3]:
            lines.append(f"  - {item.title}: {item.description}")
        for conflict in conflicts[:3]:
            lines.append(f"  ! {conflict.pair}: {conflict.severity}")
        return lines

    def _build_summary(
        self,
        recommendation: str,
        decision_confidence: float,
        evidence_strength: float,
        explainability: float,
        quality: str,
        supporting: list[EvidenceItem],
        contradicting: list[EvidenceItem],
    ) -> str:
        rec = recommendation or "No recommendation"
        support_count = len(supporting)
        contra_count = len(contradicting)
        return (
            f"{rec} | Confidence {decision_confidence:.1f}% | "
            f"Strength {evidence_strength:.1f}% | "
            f"Explainability {explainability:.1f}% ({quality}) | "
            f"{support_count} supporting, {contra_count} contradicting"
        )
