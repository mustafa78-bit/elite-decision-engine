from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from decision.evidence.dto import EvidenceItem


CONFLICT_PAIRS: list[tuple[str, str, str]] = [
    ("risk_engine", "scanner", "Risk vs Scanner"),
    ("council", "scanner", "Council vs Scanner"),
    ("portfolio", "decision", "Portfolio vs Decision"),
    ("market_regime", "scanner", "Market vs Scanner"),
    ("risk_engine", "council", "Risk vs Council"),
    ("portfolio", "scanner", "Portfolio vs Scanner"),
]


@dataclass(frozen=True)
class Conflict:
    pair: str
    severity: str
    description: str
    engine_a: str
    engine_b: str
    item_a: Optional[EvidenceItem] = None
    item_b: Optional[EvidenceItem] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "severity": self.severity,
            "description": self.description,
            "engine_a": self.engine_a,
            "engine_b": self.engine_b,
        }


def detect_conflicts(
    supporting_evidence: list[EvidenceItem],
    contradicting_evidence: list[EvidenceItem],
) -> list[Conflict]:
    conflicts: list[Conflict] = []

    engines_supporting: set[str] = {e.engine for e in supporting_evidence}
    engines_contradicting: set[str] = {e.engine for e in contradicting_evidence}

    for engine_a, engine_b, pair_name in CONFLICT_PAIRS:
        a_supports = engine_a in engines_supporting
        b_supports = engine_b in engines_supporting
        a_contradicts = engine_a in engines_contradicting
        b_contradicts = engine_b in engines_contradicting

        if a_supports and b_contradicts:
            a_items = [e for e in supporting_evidence if e.engine == engine_a]
            b_items = [e for e in contradicting_evidence if e.engine == engine_b]
            severity = _resolve_severity(a_items, b_items, engine_a, engine_b)
            conflicts.append(Conflict(
                pair=pair_name,
                severity=severity,
                description=f"{engine_a} supports but {engine_b} contradicts",
                engine_a=engine_a,
                engine_b=engine_b,
            ))

        if b_supports and a_contradicts:
            a_items = [e for e in contradicting_evidence if e.engine == engine_a]
            b_items = [e for e in supporting_evidence if e.engine == engine_b]
            severity = _resolve_severity(a_items, b_items, engine_a, engine_b)
            conflicts.append(Conflict(
                pair=pair_name,
                severity=severity,
                description=f"{engine_b} supports but {engine_a} contradicts",
                engine_a=engine_a,
                engine_b=engine_b,
            ))

    return conflicts


def _resolve_severity(
    a_items: list[EvidenceItem],
    b_items: list[EvidenceItem],
    engine_a: str,
    engine_b: str,
) -> str:
    max_sev = "LOW"
    for item in a_items + b_items:
        if item.severity == "CRITICAL":
            return "CRITICAL"
        if item.severity == "HIGH":
            max_sev = "HIGH"
        elif item.severity == "MEDIUM" and max_sev == "LOW":
            max_sev = "MEDIUM"

    if {engine_a, engine_b} == {"risk_engine", "scanner"}:
        if max_sev == "HIGH":
            return "CRITICAL"
        if max_sev == "MEDIUM":
            return "HIGH"

    return max_sev
