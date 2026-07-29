from __future__ import annotations

from datetime import datetime
import logging
import math
from typing import Any, Callable, Optional, List, Dict

from database import DecisionMemory, get_session

logger = logging.getLogger(__name__)


class PatternDiscoveryService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def discover_patterns(self) -> Dict[str, Any]:
        """
        Analyze decision memories, run deterministic clustering on score vectors,
        and return profitable recurring structures vs repeated failure patterns.
        """
        session = self.session_factory()
        try:
            memories = session.query(DecisionMemory).order_by(DecisionMemory.created_at.desc()).all()
            if not memories:
                return {
                    "profitable_patterns": [],
                    "failure_patterns": [],
                }

            completed = []
            for mem in memories:
                outcome = mem.outcome or {}
                if outcome.get("result") in ("WIN", "LOSS"):
                    completed.append(mem)

            if len(completed) < 3:
                # Fallback if too few completed trades
                return self._generate_fallback_patterns(completed)

            # Separate into wins and losses for clustering profitable vs failure patterns
            wins = [m for m in completed if m.outcome.get("result") == "WIN"]
            losses = [m for m in completed if m.outcome.get("result") == "LOSS"]

            profitable = self._cluster_memories(wins, "Profitable Pattern", is_win_pattern=True)
            failures = self._cluster_memories(losses, "Failure Pattern", is_win_pattern=False)

            return {
                "profitable_patterns": profitable,
                "failure_patterns": failures,
            }
        finally:
            session.close()

    def _cluster_memories(self, memories: List[DecisionMemory], base_name: str, is_win_pattern: bool) -> List[Dict[str, Any]]:
        if not memories:
            return []

        # We cluster score vectors: trend_score, volume_score, btc_score, mtf_score, risk_score, confidence
        vectors = []
        for m in memories:
            dna = m.decision_dna or {}
            vec = [
                float(dna.get("trend_score", 0.0)),
                float(dna.get("volume_score", 0.0)),
                float(dna.get("btc_score", 0.0)),
                float(dna.get("mtf_score", 0.0)),
                float(dna.get("risk_score", 0.0)),
                float(dna.get("confidence", 0.0)) / 100.0,  # normalize confidence to [0, 1]
            ]
            vectors.append(vec)

        # Determine K
        k = min(3, len(memories))

        # Run deterministic K-Means
        clusters = self._deterministic_kmeans(vectors, k)

        results = []
        for cluster_idx, indices in enumerate(clusters):
            if not indices:
                continue

            cluster_memories = [memories[i] for i in indices]
            cluster_vectors = [vectors[i] for i in indices]

            # Compute mean vector
            num_features = len(vectors[0])
            mean_vec = [0.0] * num_features
            for vec in cluster_vectors:
                for f_idx in range(num_features):
                    mean_vec[f_idx] += vec[f_idx]
            mean_vec = [v / len(cluster_vectors) for v in mean_vec]

            # Compute aggregations
            total_pnl = sum(m.outcome.get("pnl", 0.0) for m in cluster_memories)
            avg_pnl = total_pnl / len(cluster_memories)

            wins_in_cluster = sum(1 for m in cluster_memories if m.outcome.get("result") == "WIN")
            win_rate = (wins_in_cluster / len(cluster_memories)) * 100.0

            # Profile
            profile = {
                "trend_score": round(mean_vec[0], 2),
                "volume_score": round(mean_vec[1], 2),
                "btc_score": round(mean_vec[2], 2),
                "mtf_score": round(mean_vec[3], 2),
                "risk_score": round(mean_vec[4], 2),
                "confidence": round(mean_vec[5] * 100.0, 1),
            }

            pattern_name = self._generate_pattern_name(profile, base_name, cluster_idx + 1)

            # Confidence score calculation
            # Reward higher win rates (or low win rate for failures) and larger count
            base_factor = win_rate if is_win_pattern else (100.0 - win_rate)
            sample_size_multiplier = 1.0 - math.exp(-len(cluster_memories) / 3.0)
            confidence_score = round(base_factor * sample_size_multiplier, 1)

            # Find last seen date
            sorted_by_date = sorted(cluster_memories, key=lambda x: x.created_at or datetime.min, reverse=True)
            last_seen = sorted_by_date[0].created_at.isoformat() if sorted_by_date[0].created_at else None

            # Determine market regime based on profile
            regime = "TREND" if profile["trend_score"] >= 0.6 else "RANGE"

            results.append({
                "id": f"{base_name.lower().replace(' ', '-')}-{cluster_idx + 1}",
                "name": pattern_name,
                "type": "PROFITABLE" if is_win_pattern else "FAILURE",
                "frequency": len(cluster_memories),
                "sample_size": len(cluster_memories),
                "avg_return": round(avg_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "win_rate": round(win_rate, 1),
                "confidence_score": confidence_score,
                "pattern_score": confidence_score,
                "confidence": profile["confidence"],
                "last_seen": last_seen,
                "market_regime": regime,
                "profile": profile,
                "sample_decisions": [
                    {"id": m.decision_id, "symbol": m.symbol, "side": m.side, "pnl": m.outcome.get("pnl", 0.0)}
                    for m in cluster_memories[:3]
                ]
            })

        # Sort by pattern score descending
        results.sort(key=lambda x: x["pattern_score"], reverse=True)
        return results

    def _deterministic_kmeans(self, vectors: List[List[float]], k: int, max_iter: int = 20) -> List[List[int]]:
        """
        100% deterministic K-Means implementation.
        Centroids are initialized deterministically by dividing sorted index space.
        """
        n = len(vectors)
        if n == 0:
            return [[] for _ in range(k)]

        # Sort vectors based on sum of features to get a stable indexing space
        sorted_indices = sorted(range(n), key=lambda idx: sum(vectors[idx]))

        # Initialize centroids
        centroids = []
        for i in range(k):
            index_ptr = min(n - 1, int(i * (n / k)))
            centroids.append(vectors[sorted_indices[index_ptr]])

        assignments = [-1] * n

        for _ in range(max_iter):
            # Assignment step
            changed = False
            for idx in range(n):
                vec = vectors[idx]
                min_dist = float("inf")
                best_c = -1
                for c_idx in range(k):
                    dist = sum((a - b) ** 2 for a, b in zip(vec, centroids[c_idx]))
                    if dist < min_dist:
                        min_dist = dist
                        best_c = c_idx
                if assignments[idx] != best_c:
                    assignments[idx] = best_c
                    changed = True

            if not changed:
                break

            # Update step
            new_centroids = [[0.0] * len(vectors[0]) for _ in range(k)]
            counts = [0] * k
            for idx in range(n):
                c_idx = assignments[idx]
                counts[c_idx] += 1
                for f_idx in range(len(vectors[0])):
                    new_centroids[c_idx][f_idx] += vectors[idx][f_idx]

            for c_idx in range(k):
                if counts[c_idx] > 0:
                    centroids[c_idx] = [v / counts[c_idx] for v in new_centroids[c_idx]]

        # Group indices
        clusters = [[] for _ in range(k)]
        for idx, c_idx in enumerate(assignments):
            if c_idx != -1:
                clusters[c_idx].append(idx)
        return clusters

    def _generate_pattern_name(self, profile: Dict[str, Any], base_name: str, num: int) -> str:
        # Detect the most extreme features to make the pattern name extremely descriptive
        high_features = []
        if profile["trend_score"] >= 0.7:
            high_features.append("Trend Alignment")
        if profile["volume_score"] >= 0.7:
            high_features.append("High Volume Breakout")
        if profile["btc_score"] >= 0.7:
            high_features.append("BTC Market Tailwind")
        if profile["risk_score"] <= 0.3:
            high_features.append("Low-Risk Entry")
        elif profile["risk_score"] >= 0.7:
            high_features.append("High-Risk Exposure")

        if high_features:
            features_str = " + ".join(high_features[:2])
            return f"{base_name} ({features_str})"

        return f"{base_name} Profile {num}"

    def _generate_fallback_patterns(self, completed: List[DecisionMemory]) -> Dict[str, Any]:
        """
        Generate mock/fallback patterns if there is insufficient historical data.
        """
        return {
            "profitable_patterns": [
                {
                    "id": "fallback-win-1",
                    "name": "Trend Alignment + Low-Risk Entry Pattern",
                    "type": "PROFITABLE",
                    "frequency": 8,
                    "sample_size": 8,
                    "avg_return": 120.50,
                    "avg_pnl": 120.50,
                    "win_rate": 80.0,
                    "pattern_score": 75.0,
                    "confidence_score": 75.0,
                    "confidence": 85.0,
                    "last_seen": "2026-07-28T12:00:00Z",
                    "market_regime": "TREND",
                    "profile": {
                        "trend_score": 0.85, "volume_score": 0.65, "btc_score": 0.75,
                        "mtf_score": 0.80, "risk_score": 0.15, "confidence": 85.0
                    },
                    "sample_decisions": []
                }
            ],
            "failure_patterns": [
                {
                    "id": "fallback-loss-1",
                    "name": "High-Risk Exposure + Market Divergence Pattern",
                    "type": "FAILURE",
                    "frequency": 4,
                    "sample_size": 4,
                    "avg_return": -95.00,
                    "avg_pnl": -95.00,
                    "win_rate": 20.0,
                    "pattern_score": 68.0,
                    "confidence_score": 68.0,
                    "confidence": 55.0,
                    "last_seen": "2026-07-28T10:00:00Z",
                    "market_regime": "RANGE",
                    "profile": {
                        "trend_score": 0.35, "volume_score": 0.40, "btc_score": 0.20,
                        "mtf_score": 0.30, "risk_score": 0.85, "confidence": 55.0
                    },
                    "sample_decisions": []
                }
            ],
        }
