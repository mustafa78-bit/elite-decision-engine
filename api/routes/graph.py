from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from decision.kernel.KnowledgeGraph import GraphNode, KnowledgeGraph
from decision.kernel.DecisionLedger import DecisionLedger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])

# Instantiate single global KnowledgeGraph and Ledger managers
_knowledge_graph = KnowledgeGraph()
_ledger = DecisionLedger()


class NodeCreateRequest(BaseModel):
    id: str
    type: str
    name: str
    confidence: float = 1.0
    trust: float = 1.0
    influence_score: float = 1.0
    importance_score: float = 1.0
    properties: dict[str, Any] = {}


class EdgeCreateRequest(BaseModel):
    source_id: str
    target_id: str
    type: str
    weight: float = 1.0
    confidence: float = 1.0
    trust: float = 1.0
    properties: dict[str, Any] = {}


@router.get("/nodes")
def list_graph_nodes(type: Optional[str] = None):
    """Retrieve all active understanding nodes registered in Knowledge Graph 2.0."""
    try:
        nodes = list(_knowledge_graph.nodes.values())
        if type:
            nodes = [n for n in nodes if n.type.lower() == type.lower()]
        return {
            "status": "success",
            "nodes": [n.__dict__ for n in nodes]
        }
    except Exception as e:
        logger.exception("Failed to list graph nodes")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes")
def add_graph_node(req: NodeCreateRequest):
    """Register a new node inside the Knowledge Graph."""
    try:
        node = GraphNode(
            id=req.id,
            type=req.type,
            name=req.name,
            confidence=req.confidence,
            trust=req.trust,
            influence_score=req.influence_score,
            importance_score=req.importance_score,
            properties=req.properties,
        )
        _knowledge_graph.add_node(node)
        return {"status": "success", "node_id": req.id}
    except Exception as e:
        logger.exception("Failed to register node")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges")
def add_graph_edge(req: EdgeCreateRequest):
    """Create a semantic relationship edge between two nodes."""
    try:
        _knowledge_graph.add_edge(
            source_id=req.source_id,
            target_id=req.target_id,
            type=req.type,
            weight=req.weight,
            confidence=req.confidence,
            trust=req.trust,
            properties=req.properties,
        )
        return {"status": "success", "source": req.source_id, "target": req.target_id}
    except Exception as e:
        logger.exception("Failed to create edge")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subgraph/{node_id}")
def get_local_subgraph(node_id: str, depth: int = 2):
    """Extract a semantic neighborhood around the target node."""
    try:
        subgraph = _knowledge_graph.subgraph_extraction(node_id, max_depth=depth)
        return {
            "status": "success",
            "node_id": node_id,
            "depth": depth,
            "subgraph": subgraph,
        }
    except Exception as e:
        logger.exception("Failed to extract subgraph")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/why/{node_id}")
def query_graph_why(node_id: str):
    """Query the causal explanation and backing evidence for any node."""
    try:
        explanation = _knowledge_graph.why(node_id)
        return {
            "status": "success",
            "node_id": node_id,
            "explanation": explanation,
        }
    except Exception as e:
        logger.exception("Failed to query explanation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/counterfactual/{node_id}")
def query_counterfactual(node_id: str):
    """Evaluate what happens to downstream dependencies if this node is removed."""
    try:
        impact = _knowledge_graph.what_happens_if_removed(node_id)
        return {
            "status": "success",
            "node_id": node_id,
            "impact_analysis": impact,
        }
    except Exception as e:
        logger.exception("Failed to perform counterfactual simulation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{node_id}")
def query_forecast(node_id: str):
    """Predict likely future states using forward traversal from this node."""
    try:
        forecast = _knowledge_graph.what_will_likely_happen_next(node_id)
        return {
            "status": "success",
            "node_id": node_id,
            "forecast_analysis": forecast,
        }
    except Exception as e:
        logger.exception("Failed to predict next states")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ledger")
def get_graph_ledger():
    """Retrieve all decision records logged in the Decision Ledger."""
    try:
        return {
            "status": "success",
            "ledger": _ledger.get_all_records()
        }
    except Exception as e:
        logger.exception("Failed to query ledger")
        raise HTTPException(status_code=500, detail=str(e))


def get_global_knowledge_graph() -> KnowledgeGraph:
    """Dependency helper to resolve global KnowledgeGraph."""
    return _knowledge_graph
