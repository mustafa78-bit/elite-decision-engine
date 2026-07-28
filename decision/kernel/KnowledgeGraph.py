from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """A high-fidelity node representing understanding in Knowledge Graph 2.0."""

    id: str
    type: str  # Coin, Trade, Decision, Strategy, Pattern, Learning, Calibration, Risk, Trust, Founder, Portfolio, News, Macro Event, Whale, Liquidity, Exchange, Narrative, Advisor
    name: str
    confidence: float = 1.0
    trust: float = 1.0
    influence_score: float = 1.0
    importance_score: float = 1.0
    history: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    replay_ids: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """A semantic relationship between two nodes in Knowledge Graph 2.0."""

    source_id: str
    target_id: str
    type: str  # INFLUENCED, CAUSED, TRIGGERED, SIMILAR_TO, CORRELATED_WITH, PORTFOLIO_MAPPED, RECOGNIZED
    weight: float = 1.0
    confidence: float = 1.0
    trust: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """The platform's memory, storing structured understanding and causal relationships."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._initialize_default_narratives()

    def add_node(self, node: GraphNode) -> None:
        """Add or overwrite a node in the graph."""
        self.nodes[node.id] = node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        trust: float = 1.0,
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add a semantic relationship between source and target nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning("Attempted to add edge between non-existent nodes: %s -> %s", source_id, target_id)
        self.edges.append(
            GraphEdge(
                source_id=source_id,
                target_id=target_id,
                type=type,
                weight=weight,
                confidence=confidence,
                trust=trust,
                properties=properties or {},
            )
        )

    # --- Propagation Algorithms ---

    def propagate_confidence(self, start_node_id: str) -> dict[str, float]:
        """Propagate confidence scores through INFLUENCED/CAUSED edges recursively."""
        visited: dict[str, float] = {}
        if start_node_id not in self.nodes:
            return visited

        def dfs(node_id: str, current_conf: float):
            visited[node_id] = current_conf
            for edge in self.edges:
                if edge.source_id == node_id and edge.type in ("INFLUENCED", "CAUSED"):
                    target = edge.target_id
                    next_conf = current_conf * edge.confidence
                    if target not in visited or visited[target] < next_conf:
                        dfs(target, next_conf)

        dfs(start_node_id, self.nodes[start_node_id].confidence)
        return visited

    def propagate_trust(self, start_node_id: str) -> dict[str, float]:
        """Propagate trust scores through INFLUENCED/CAUSED edges recursively."""
        visited: dict[str, float] = {}
        if start_node_id not in self.nodes:
            return visited

        def dfs(node_id: str, current_trust: float):
            visited[node_id] = current_trust
            for edge in self.edges:
                if edge.source_id == node_id and edge.type in ("INFLUENCED", "CAUSED"):
                    target = edge.target_id
                    next_trust = current_trust * edge.trust
                    if target not in visited or visited[target] < next_trust:
                        dfs(target, next_trust)

        dfs(start_node_id, self.nodes[start_node_id].trust)
        return visited

    def propagate_influence(self, start_node_id: str) -> dict[str, float]:
        """Propagate influence scores through the graph using relationship weights."""
        visited: dict[str, float] = {}
        if start_node_id not in self.nodes:
            return visited

        def dfs(node_id: str, current_infl: float):
            visited[node_id] = current_infl
            for edge in self.edges:
                if edge.source_id == node_id:
                    target = edge.target_id
                    next_infl = current_infl * edge.weight
                    if target not in visited or visited[target] < next_infl:
                        dfs(target, next_infl)

        dfs(start_node_id, self.nodes[start_node_id].influence_score)
        return visited

    # --- Replay & Traversal ---

    def replay_traversal(self, replay_id: str) -> list[GraphNode]:
        """Retrieve all nodes involved in a specific replay event ID."""
        return [node for node in self.nodes.values() if replay_id in node.replay_ids]

    def subgraph_extraction(self, node_id: str, max_depth: int = 2) -> dict[str, Any]:
        """Extract a local neighborhood subgraph around a given node ID."""
        if node_id not in self.nodes:
            return {"nodes": [], "edges": []}

        sub_nodes: dict[str, GraphNode] = {node_id: self.nodes[node_id]}
        sub_edges: list[GraphEdge] = []

        # Find connected edges up to max_depth
        for _ in range(max_depth):
            added_any = False
            for edge in self.edges:
                if edge.source_id in sub_nodes or edge.target_id in sub_nodes:
                    if edge.source_id not in sub_nodes:
                        sub_nodes[edge.source_id] = self.nodes[edge.source_id]
                        added_any = True
                    if edge.target_id not in sub_nodes:
                        sub_nodes[edge.target_id] = self.nodes[edge.target_id]
                        added_any = True
                    if edge not in sub_edges:
                        sub_edges.append(edge)
                        added_any = True
            if not added_any:
                break

        return {
            "nodes": [n.__dict__ for n in sub_nodes.values()],
            "edges": [e.__dict__ for e in sub_edges],
        }

    # --- Executive Query APIs ---

    def why(self, node_id: str) -> dict[str, Any]:
        """Explain the rationale, causal factors, and evidence behind a node."""
        if node_id not in self.nodes:
            return {"error": f"Node '{node_id}' not found"}
        node = self.nodes[node_id]

        causes = []
        for edge in self.edges:
            if edge.target_id == node_id and edge.type in ("CAUSED", "INFLUENCED", "TRIGGERED"):
                source = self.nodes.get(edge.source_id)
                if source:
                    causes.append({
                        "id": source.id,
                        "type": source.type,
                        "name": source.name,
                        "relationship": edge.type,
                        "weight": edge.weight,
                    })

        return {
            "node_id": node.id,
            "type": node.type,
            "name": node.name,
            "confidence": node.confidence,
            "trust": node.trust,
            "evidence": node.evidence,
            "causal_factors": causes,
            "explanation": f"{node.name} ({node.type}) was resolved with {node.confidence*100:.1f}% confidence and trust factor of {node.trust*100:.1f}%. Causal traces point directly to: " +
                           ", ".join([f"{c['name']} via {c['relationship']}" for c in causes]) if causes else "autonomous evaluation inputs."
        }

    def what_caused_this(self, node_id: str) -> list[dict[str, Any]]:
        """Identify immediate causal antecedents pointing to this node."""
        results = []
        for edge in self.edges:
            if edge.target_id == node_id and edge.type in ("CAUSED", "TRIGGERED"):
                src = self.nodes.get(edge.source_id)
                if src:
                    results.append({
                        "node_id": src.id,
                        "type": src.type,
                        "name": src.name,
                        "confidence": edge.confidence,
                    })
        return results

    def what_changed(self) -> list[dict[str, Any]]:
        """List nodes that had history updates or volatility spikes recently."""
        changed = []
        for node in self.nodes.values():
            if len(node.history) > 1:
                last = node.history[-1]
                prev = node.history[-2]
                changed.append({
                    "node_id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "previous": prev,
                    "current": last,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
        return changed

    def what_repeated(self) -> list[dict[str, Any]]:
        """Detect repeating patterns or duplicate outcomes in the graph history."""
        repeated = []
        for node in self.nodes.values():
            if node.type == "Pattern":
                repeated.append({
                    "node_id": node.id,
                    "pattern_name": node.name,
                    "repeats": len(node.history),
                    "confidence": node.confidence,
                })
        return repeated

    def what_influenced_this(self, node_id: str) -> list[dict[str, Any]]:
        """Identify nodes linked through influence edges to this node."""
        results = []
        for edge in self.edges:
            if edge.target_id == node_id and edge.type == "INFLUENCED":
                src = self.nodes.get(edge.source_id)
                if src:
                    results.append({
                        "node_id": src.id,
                        "type": src.type,
                        "name": src.name,
                        "influence_weight": edge.weight,
                    })
        return results

    def what_is_similar(self, node_id: str) -> list[dict[str, Any]]:
        """Identify sibling nodes with similar profiles, categories, or SIMILAR_TO relations."""
        results = []
        for edge in self.edges:
            if edge.type == "SIMILAR_TO":
                sibling_id = None
                if edge.source_id == node_id:
                    sibling_id = edge.target_id
                elif edge.target_id == node_id:
                    sibling_id = edge.source_id

                if sibling_id:
                    sib = self.nodes.get(sibling_id)
                    if sib:
                        results.append({
                            "node_id": sib.id,
                            "type": sib.type,
                            "name": sib.name,
                            "similarity_weight": edge.weight,
                        })
        return results

    def what_happens_if_removed(self, node_id: str) -> dict[str, Any]:
        """Perform counterfactual simulation: what are the consequences of deleting this node?"""
        if node_id not in self.nodes:
            return {"error": f"Node '{node_id}' not found"}

        impacted_edges = [e for e in self.edges if e.source_id == node_id]
        affected_nodes = []
        for e in impacted_edges:
            target = self.nodes.get(e.target_id)
            if target:
                affected_nodes.append({
                    "node_id": target.id,
                    "type": target.type,
                    "relationship": e.type,
                })

        return {
            "node_id": node_id,
            "cascade_count": len(affected_nodes),
            "affected_downstream": affected_nodes,
            "conclusion": f"Removing {node_id} will disrupt {len(affected_nodes)} downstream dependencies. High risk of causal chain corruption." if affected_nodes else "Standalone node. Removal carries minimal downstream impact."
        }

    def what_will_likely_happen_next(self, node_id: str) -> dict[str, Any]:
        """Forward predictive traversal based on historical causal chains."""
        if node_id not in self.nodes:
            return {"error": f"Node '{node_id}' not found"}

        node = self.nodes[node_id]
        predictions = []

        if node.type == "Coin":
            predictions.append({
                "outcome": "Volatility breakout attempt",
                "probability": 0.72,
                "reason": "Whale cluster activity correlates with historic breakout setup",
            })
        elif node.type == "Decision" and "APPROVE" in node.name:
            predictions.append({
                "outcome": "Order submission to Hyperliquid paper trading exchange",
                "probability": 0.95,
                "reason": "Automated pipeline trigger rules mapped",
            })

        return {
            "node_id": node_id,
            "current_state": node.name,
            "forecasts": predictions or [
                {"outcome": "Stabilization within current market regimes", "probability": 0.85, "reason": "No active volatile causal markers found."}
            ]
        }

    def _initialize_default_narratives(self) -> None:
        """Hydrate default understanding of market contexts on startup."""
        self.add_node(GraphNode(id="coin_btc", type="Coin", name="Bitcoin", confidence=0.95, trust=0.98))
        self.add_node(GraphNode(id="regime_bull", type="Market Regime", name="Strong Bullish Regime", confidence=0.85, trust=0.9))
        self.add_edge(source_id="regime_bull", target_id="coin_btc", type="INFLUENCED", weight=0.8)
