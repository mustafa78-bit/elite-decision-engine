from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from dto.coordination import (
    ConfidenceAggregationDTO,
    ConflictResolutionDTO,
    ConsensusScoreDTO,
    CoordinatorDiagnosticsDTO,
    CoordinatorReportDTO,
    IntelligenceSourceDTO,
    RecommendationRankingDTO,
    SourcePriorityDTO,
)

logger = logging.getLogger(__name__)


class IntelligenceRegistry:
    """Registry of all available intelligence sources."""

    def __init__(self) -> None:
        self._sources: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        source_type: str,
        instance: Any,
        weight: float = 1.0,
        priority: int = 0,
    ) -> None:
        self._sources[name] = {
            "name": name,
            "source_type": source_type,
            "instance": instance,
            "weight": weight,
            "priority": priority,
            "available": True,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "latency_ms": 0.0,
            "error_count": 0,
        }
        logger.info("Registered intelligence source: %s (type=%s, weight=%.2f)", name, source_type, weight)

    def unregister(self, name: str) -> None:
        self._sources.pop(name, None)

    def get(self, name: str) -> Optional[dict[str, Any]]:
        return self._sources.get(name)

    def list_sources(self) -> list[dict[str, Any]]:
        return [
            {k: v for k, v in s.items() if k != "instance"}
            for s in self._sources.values()
        ]

    def get_instance(self, name: str) -> Any:
        src = self._sources.get(name)
        return src["instance"] if src else None

    def all_instances(self) -> list[Any]:
        return [s["instance"] for s in self._sources.values()]

    @property
    def count(self) -> int:
        return len(self._sources)

    def mark_error(self, name: str) -> None:
        src = self._sources.get(name)
        if src:
            src["error_count"] = src.get("error_count", 0) + 1

    def mark_latency(self, name: str, latency_ms: float) -> None:
        src = self._sources.get(name)
        if src:
            src["latency_ms"] = latency_ms
            src["last_updated"] = datetime.now(timezone.utc).isoformat()


class AISourceRegistry:
    """Registry of AI analysis sources with prioritization."""

    def __init__(self) -> None:
        self._sources: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        version: str = "1.0",
        weight: float = 1.0,
        priority: int = 5,
        capabilities: Optional[list[str]] = None,
    ) -> None:
        self._sources[name] = {
            "name": name,
            "version": version,
            "weight": weight,
            "priority": priority,
            "capabilities": capabilities or [],
            "active": True,
        }

    def set_active(self, name: str, active: bool) -> None:
        if name in self._sources:
            self._sources[name]["active"] = active

    def get_priorities(self) -> list[SourcePriorityDTO]:
        sorted_sources = sorted(
            self._sources.values(),
            key=lambda s: (s["priority"], s["weight"]),
            reverse=True,
        )
        return [
            SourcePriorityDTO(
                source_name=s["name"],
                priority=s["priority"],
                weight=s["weight"],
                is_active=s["active"],
            )
            for s in sorted_sources
        ]

    def list_sources(self) -> list[dict[str, Any]]:
        return list(self._sources.values())

    @property
    def count(self) -> int:
        return len(self._sources)


class CoordinatorService:
    """Central AI coordination layer for aggregating intelligence from multiple sources.

    Responsibilities:
    - Register and prioritize intelligence sources
    - Aggregate confidence scores with weighting
    - Resolve conflicts between sources
    - Compute consensus scores
    - Rank recommendations
    - Provide diagnostics
    """

    def __init__(self) -> None:
        self.intelligence_registry = IntelligenceRegistry()
        self.ai_source_registry = AISourceRegistry()
        self._evaluation_count = 0
        self._conflict_count = 0
        self._total_processing_time = 0.0
        self._start_time = time.time()
        self._errors_last_hour = 0
        self._last_error_reset = time.time()

    def evaluate(self, signal: Any, scores: Optional[dict[str, Any]] = None) -> CoordinatorReportDTO:
        start = time.perf_counter()
        self._evaluation_count += 1

        self._reset_error_counter_if_needed()

        aggregations = self._aggregate_confidences(signal, scores)
        conflicts = self._resolve_conflicts(aggregations)
        consensus = self._compute_consensus(aggregations, conflicts)
        priorities = self.ai_source_registry.get_priorities()
        recommendations = self._rank_recommendations(signal, scores, consensus)
        diagnostics = self._build_diagnostics()

        elapsed = (time.perf_counter() - start) * 1000
        self._total_processing_time += elapsed

        return CoordinatorReportDTO(
            consensus=consensus,
            aggregations=aggregations,
            conflicts=conflicts,
            priorities=priorities,
            recommendations=recommendations,
            diagnostics=diagnostics,
        )

    def _aggregate_confidences(
        self, signal: Any, scores: Optional[dict[str, Any]]
    ) -> list[ConfidenceAggregationDTO]:
        results: list[ConfidenceAggregationDTO] = []

        for src in self.intelligence_registry.list_sources():
            name = src["name"]
            weight = src.get("weight", 1.0)

            try:
                instance = self.intelligence_registry.get_instance(name)
                raw_conf = 0.5
                if instance is not None and hasattr(instance, "score"):
                    if scores:
                        sig_result = instance.score(signal) if hasattr(instance, "score") else None
                        if sig_result and isinstance(sig_result, dict):
                            raw_conf = sig_result.get("final_score", raw_conf)
                elif scores:
                    raw_conf = scores.get("final_score", raw_conf)

                weighted = raw_conf * weight
                adjusted = weight != 1.0
                results.append(ConfidenceAggregationDTO(
                    source_name=name,
                    raw_confidence=round(raw_conf, 4),
                    weighted_confidence=round(weighted, 4),
                    weight=weight,
                    adjusted=adjusted,
                    adjustment_reason=f"Weighted by {weight}" if adjusted else "",
                ))
            except Exception as e:
                logger.warning("Source %s aggregation failed: %s", name, e)
                self.intelligence_registry.mark_error(name)
                self._errors_last_hour += 1

        return results

    def _resolve_conflicts(
        self, aggregations: list[ConfidenceAggregationDTO]
    ) -> list[ConflictResolutionDTO]:
        conflicts: list[ConflictResolutionDTO] = []
        if len(aggregations) < 2:
            return conflicts

        for i in range(len(aggregations)):
            for j in range(i + 1, len(aggregations)):
                a = aggregations[i]
                b = aggregations[j]
                diff = abs(a.weighted_confidence - b.weighted_confidence)
                if diff > 0.3:
                    self._conflict_count += 1
                    resolved = (a.weighted_confidence + b.weighted_confidence) / 2
                    conflicts.append(ConflictResolutionDTO(
                        source_a=a.source_name,
                        source_b=b.source_name,
                        value_a=a.weighted_confidence,
                        value_b=b.weighted_confidence,
                        resolved_value=round(resolved, 4),
                        resolution_strategy="average",
                        resolution_reason=f"Conflict detected: diff={diff:.2f} > 0.3",
                    ))

        return conflicts

    def _compute_consensus(
        self,
        aggregations: list[ConfidenceAggregationDTO],
        conflicts: list[ConflictResolutionDTO],
    ) -> ConsensusScoreDTO:
        if not aggregations:
            return ConsensusScoreDTO()

        values = [a.weighted_confidence for a in aggregations]
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values) if len(values) > 1 else 0.0

        agreeing = sum(1 for v in values if abs(v - mean_val) <= 0.2)
        disagreeing = len(values) - agreeing

        agreement_level = "strong"
        if disagreeing > agreeing:
            agreement_level = "weak"
        elif variance > 0.1:
            agreement_level = "moderate"

        return ConsensusScoreDTO(
            final_score=round(mean_val, 4),
            agreement_level=agreement_level,
            source_count=len(aggregations),
            sources_agreeing=agreeing,
            sources_disagreeing=disagreeing,
            variance=round(variance, 6),
        )

    def _rank_recommendations(
        self,
        signal: Any,
        scores: Optional[dict[str, Any]],
        consensus: ConsensusScoreDTO,
    ) -> list[RecommendationRankingDTO]:
        result: list[RecommendationRankingDTO] = []

        signal_id = getattr(signal, "id", 0) if signal else 0
        symbol = getattr(signal, "symbol", "?") if signal else "?"
        side = getattr(signal, "side", "?") if signal else "?"

        final = consensus.final_score if consensus else 0
        rec = "PASS"
        reasons = []

        if final >= 0.8:
            rec = "STRONG_BUY"
            reasons.append("Strong consensus across sources")
        elif final >= 0.6:
            rec = "BUY"
            reasons.append("Moderate consensus across sources")
        elif final >= 0.4:
            rec = "WATCH"
            reasons.append("Weak consensus")
        else:
            reasons.append("Below threshold")

        src_count = consensus.source_count if consensus else 0
        result.append(RecommendationRankingDTO(
            rank=1,
            signal_id=signal_id,
            symbol=symbol,
            side=side,
            composite_score=round(final, 4),
            recommendation=rec,
            reasons=reasons,
            sources_evaluated=src_count,
        ))

        return result

    def _build_diagnostics(self) -> CoordinatorDiagnosticsDTO:
        elapsed = time.time() - self._start_time
        avg_ms = (self._total_processing_time / self._evaluation_count) if self._evaluation_count > 0 else 0.0

        sources = self.intelligence_registry.list_sources()
        availability: dict[str, bool] = {s["name"]: s.get("available", False) for s in sources}
        latency: dict[str, float] = {s["name"]: s.get("latency_ms", 0.0) for s in sources}

        return CoordinatorDiagnosticsDTO(
            total_evaluations=self._evaluation_count,
            total_conflicts=self._conflict_count,
            conflicts_resolved=self._conflict_count,
            avg_processing_time_ms=round(avg_ms, 2),
            source_availability=availability,
            source_latency=latency,
            errors_last_hour=self._errors_last_hour,
            uptime_seconds=round(elapsed, 2),
        )

    def _reset_error_counter_if_needed(self) -> None:
        now = time.time()
        if now - self._last_error_reset > 3600:
            self._errors_last_hour = 0
            self._last_error_reset = now
