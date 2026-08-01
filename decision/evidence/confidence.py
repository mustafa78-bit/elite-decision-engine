from __future__ import annotations

from typing import Any


SUPPORTING_WEIGHT = 1.0
CONTRADICTING_WEIGHT = 1.2

SEVERITY_WEIGHTS = {"LOW": 0.5, "MEDIUM": 1.0, "HIGH": 1.5, "CRITICAL": 2.0}

SOURCE_WEIGHTS: dict[str, float] = {
    "scanner": 0.9,
    "council": 1.0,
    "risk_engine": 1.2,
    "portfolio": 0.8,
    "market_regime": 0.9,
    "whale": 0.6,
    "explain": 0.7,
    "decision": 1.0,
    "evidence_engine": 1.0,
}

STRENGTH_WEIGHTS: dict[str, float] = {
    "scanner": 0.85,
    "council": 0.90,
    "risk_engine": 0.95,
    "portfolio": 0.75,
    "market_regime": 0.80,
    "whale": 0.60,
    "explain": 0.70,
    "decision": 0.90,
    "evidence_engine": 0.95,
}


def calculate_confidence(
    supporting_evidence: list[Any],
    contradicting_evidence: list[Any],
) -> float:
    if not supporting_evidence and not contradicting_evidence:
        return 0.0

    support_score = 0.0
    for item in supporting_evidence:
        sv = SEVERITY_WEIGHTS.get(item.severity, 1.0)
        ew = SOURCE_WEIGHTS.get(item.engine, 0.5)
        cw = getattr(item, "weight", 1.0)
        support_score += sv * ew * cw * item.confidence * SUPPORTING_WEIGHT

    contradict_score = 0.0
    for item in contradicting_evidence:
        sv = SEVERITY_WEIGHTS.get(item.severity, 1.0)
        ew = SOURCE_WEIGHTS.get(item.engine, 0.5)
        cw = getattr(item, "weight", 1.0)
        contradict_score += sv * ew * cw * item.confidence * CONTRADICTING_WEIGHT

    total = support_score + contradict_score
    if total == 0.0:
        return 0.0

    net = (support_score - contradict_score) / total
    confidence = (net + 1.0) * 50.0
    return max(0.0, min(100.0, round(confidence, 1)))


def calculate_evidence_strength(supporting_evidence: list[Any]) -> float:
    if not supporting_evidence:
        return 0.0

    total = 0.0
    max_possible = 0.0

    for item in supporting_evidence:
        sv = SEVERITY_WEIGHTS.get(item.severity, 1.0)
        ew = STRENGTH_WEIGHTS.get(item.engine, 0.5)
        cw = getattr(item, "weight", 1.0)
        total += sv * ew * cw * item.confidence
        max_possible += sv * ew * cw

    if max_possible == 0.0:
        return 0.0

    strength = (total / max_possible) * 100.0
    return max(0.0, min(100.0, round(strength, 1)))


def calculate_explainability(
    supporting_evidence: list[Any],
    contradicting_evidence: list[Any],
    sources: list[Any],
    timeline_count: int,
) -> float:
    if not supporting_evidence and not contradicting_evidence:
        return 0.0

    total_items = len(supporting_evidence) + len(contradicting_evidence)
    if total_items == 0:
        return 0.0

    coverage = min(1.0, total_items / 5.0)
    source_diversity = min(1.0, len(sources) / 3.0)
    timeline_factor = min(1.0, timeline_count / 3.0)
    contradict_visibility = 1.0 if contradicting_evidence else 0.5

    score = (coverage * 0.35 + source_diversity * 0.30 + timeline_factor * 0.20 + contradict_visibility * 0.15) * 100.0
    return max(0.0, min(100.0, round(score, 1)))


def calculate_decision_quality(
    decision_confidence: float,
    evidence_strength: float,
    explainability: float,
    support_count: int,
    contradict_count: int,
) -> str:
    composite = (decision_confidence * 0.4 + evidence_strength * 0.35 + explainability * 0.25)
    if composite >= 80 and support_count >= 2 and contradict_count == 0:
        return "STRONG"
    if composite >= 60 and support_count >= 1:
        return "MODERATE"
    if composite >= 30:
        return "WEAK"
    return "INSUFFICIENT"
