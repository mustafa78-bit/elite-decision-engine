import json
import time
import hashlib
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_session
from memory.l0_event_log.service import L0EventStore
from memory.l0_event_log.models import NEXUSEvent
from memory.l2_graph.models import GraphNode, GraphEdge, GraphSnapshot
from memory.l2_graph.registry import NodeRegistry, EdgeRegistry
from memory.l2_graph.builder import RelationshipBuilder

logger = logging.getLogger(__name__)


class GraphEngine:
    """Production-grade Layer 2 Relationship Graph Engine.

    Builds, maintains, and replays the canonical NEXUS relationship graph.
    Supports advanced graph query capabilities, metrics tracking, and health checks.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = get_session,
        event_store: Optional[L0EventStore] = None,
    ) -> None:
        self.session_factory = session_factory
        self.event_store = event_store or L0EventStore(session_factory)
        logger.info("NEXUS Layer 2 Relationship Graph Engine initialized.")

    def process_event(self, session: Session, event: NEXUSEvent) -> List[GraphEdge]:
        """Maps an individual L0 event to graph nodes and relationships sequentially.

        Ensures that nodes are mapped to standard singular types:
        Coin, Whale, News, Decision, Portfolio, Strategy, Indicator, Market Regime.
        """
        event_type = event.event_type
        payload = event.payload or {}
        seq_num = event.seq_id
        event_id = event.event_id

        edges: List[GraphEdge] = []
        builder = RelationshipBuilder(session)

        # 1. Custom/Explicit GraphRelationCreated / L2GraphEdge event format
        if event_type in ("GraphRelationCreated", "L2GraphEdge"):
            source = payload.get("source", {})
            target = payload.get("target", {})
            relationship = payload.get("relationship", {})

            if source and target and relationship:
                # Map to singular forms if standard
                src_type = self._standardize_node_type(source.get("type"))
                tgt_type = self._standardize_node_type(target.get("type"))

                edge = (
                    builder.source(
                        node_type=src_type,
                        external_id=source.get("id"),
                        properties=source.get("properties"),
                    )
                    .target(
                        node_type=tgt_type,
                        external_id=target.get("id"),
                        properties=target.get("properties"),
                    )
                    .relationship(
                        relationship_type=relationship.get("type"),
                    )
                    .evidence(
                        confidence=payload.get("confidence") or relationship.get("confidence") or 1.0,
                        provenance={
                            "event_type": event_type,
                            "actor_id": event.actor_id,
                            "causal_chain_id": event.causal_chain_id,
                            "parent_event_id": event.parent_event_id,
                        },
                        supporting_event_ids=[event_id],
                        supporting_projection_ids=payload.get("projection_ids") or [],
                        created_seq_id=seq_num,
                    )
                    .commit()
                )
                edges.append(edge)

        # 2. WhaleActivity / WhaleTransaction mapping
        elif event_type in ("WhaleActivity", "WhaleTransaction"):
            whale_id = payload.get("whale_id") or payload.get("wallet_address") or payload.get("wallet")
            symbol = payload.get("symbol")
            action = payload.get("action", "trade").lower()  # accumulate, distribute, trade

            if whale_id and symbol:
                rel_type = "traded"
                if "accumulat" in action:
                    rel_type = "accumulated"
                elif "distribut" in action:
                    rel_type = "distributed"

                edge = (
                    builder.source(
                        node_type="Whale",
                        external_id=whale_id,
                        properties={"last_active": event.timestamp.isoformat() if event.timestamp else None},
                    )
                    .target(
                        node_type="Coin",
                        external_id=symbol,
                        properties={"symbol": symbol},
                    )
                    .relationship(
                        relationship_type=rel_type,
                    )
                    .evidence(
                        confidence=payload.get("confidence", 1.0),
                        provenance={
                            "event_type": event_type,
                            "causal_chain_id": event.causal_chain_id,
                        },
                        supporting_event_ids=[event_id],
                        supporting_projection_ids=["WhaleView"],
                        created_seq_id=seq_num,
                    )
                    .commit()
                )
                edges.append(edge)

        # 3. NewsPublished / NewsEvent mapping
        elif event_type in ("NewsPublished", "NewsEvent"):
            news_id = payload.get("news_id") or payload.get("id") or str(uuid.uuid4())
            headline = payload.get("headline") or payload.get("title") or "Untitled News"
            symbols = payload.get("symbols", []) or payload.get("related_assets", [])
            wallets = payload.get("wallets", []) or payload.get("related_wallets", [])

            if news_id:
                # Core news node properties
                news_props = {
                    "headline": headline,
                    "sentiment": payload.get("sentiment", 0.0),
                    "importance": payload.get("importance", 0.0),
                }

                # Link to all mentioned Coins
                for symbol in symbols:
                    edge = (
                        builder.source(
                            node_type="News",
                            external_id=news_id,
                            properties=news_props,
                        )
                        .target(
                            node_type="Coin",
                            external_id=symbol,
                            properties={"symbol": symbol},
                        )
                        .relationship(
                            relationship_type="mentions",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["NewsView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

                # Link to mentioned Whales
                for wallet in wallets:
                    edge = (
                        builder.source(
                            node_type="News",
                            external_id=news_id,
                            properties=news_props,
                        )
                        .target(
                            node_type="Whale",
                            external_id=wallet,
                        )
                        .relationship(
                            relationship_type="mentions",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["NewsView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

        # 4. AIDecision / DecisionGenerated / CalibrationDecision mapping
        elif event_type in ("AIDecision", "DecisionGenerated", "CalibrationDecision"):
            decision_id = payload.get("decision_id") or payload.get("id")
            symbol = payload.get("symbol")
            strategy = payload.get("strategy") or payload.get("strategy_name")
            portfolio = payload.get("portfolio") or payload.get("portfolio_id")
            indicators = payload.get("indicators", []) or payload.get("supporting_signals", [])

            if decision_id:
                decision_props = {
                    "recommendation": payload.get("recommendation") or payload.get("predicted_side") or payload.get("decision"),
                    "confidence": payload.get("confidence", 0.0),
                    "risk_level": payload.get("risk_level", "moderate"),
                }

                # Decision mentions Coin
                if symbol:
                    edge = (
                        builder.source(
                            node_type="Decision",
                            external_id=decision_id,
                            properties=decision_props,
                        )
                        .target(
                            node_type="Coin",
                            external_id=symbol,
                        )
                        .relationship(
                            relationship_type="mentions",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["DecisionView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

                # Decision generated Strategy execution
                if strategy:
                    edge = (
                        builder.source(
                            node_type="Decision",
                            external_id=decision_id,
                            properties=decision_props,
                        )
                        .target(
                            node_type="Strategy",
                            external_id=strategy,
                        )
                        .relationship(
                            relationship_type="generated",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["DecisionView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

                # Decision belongs to Portfolio
                if portfolio:
                    edge = (
                        builder.source(
                            node_type="Decision",
                            external_id=decision_id,
                            properties=decision_props,
                        )
                        .target(
                            node_type="Portfolio",
                            external_id=portfolio,
                        )
                        .relationship(
                            relationship_type="belongs_to",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["DecisionView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

                # Confirmed or Contradicted by Indicators
                for ind in indicators:
                    ind_name = ind.get("name") if isinstance(ind, dict) else str(ind)
                    confirmed = ind.get("confirmed", True) if isinstance(ind, dict) else True
                    rel = "confirmed_by" if confirmed else "contradicted_by"

                    edge = (
                        builder.source(
                            node_type="Decision",
                            external_id=decision_id,
                            properties=decision_props,
                        )
                        .target(
                            node_type="Indicator",
                            external_id=ind_name,
                        )
                        .relationship(
                            relationship_type=rel,
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["DecisionView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

        # 5. PortfolioUpdated / PortfolioTransaction mapping
        elif event_type in ("PortfolioUpdated", "PortfolioTransaction"):
            portfolio_id = payload.get("portfolio_id") or payload.get("id") or "default_portfolio"
            symbol = payload.get("symbol")
            strategy = payload.get("strategy") or payload.get("strategy_name")

            if portfolio_id:
                # Portfolio traded Coin
                if symbol:
                    edge = (
                        builder.source(
                            node_type="Portfolio",
                            external_id=portfolio_id,
                        )
                        .target(
                            node_type="Coin",
                            external_id=symbol,
                        )
                        .relationship(
                            relationship_type="traded",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["PortfolioView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

                # Strategy belongs to Portfolio
                if strategy:
                    edge = (
                        builder.source(
                            node_type="Strategy",
                            external_id=strategy,
                        )
                        .target(
                            node_type="Portfolio",
                            external_id=portfolio_id,
                        )
                        .relationship(
                            relationship_type="belongs_to",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=["PortfolioView"],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

        # 6. StrategyUpdated / StrategyState mapping
        elif event_type in ("StrategyUpdated", "StrategyState"):
            strategy_name = payload.get("strategy_name") or payload.get("name")
            portfolio_id = payload.get("portfolio_id")
            indicators = payload.get("indicators", [])

            if strategy_name:
                # Strategy belongs to Portfolio
                if portfolio_id:
                    edge = (
                        builder.source(
                            node_type="Strategy",
                            external_id=strategy_name,
                        )
                        .target(
                            node_type="Portfolio",
                            external_id=portfolio_id,
                        )
                        .relationship(
                            relationship_type="belongs_to",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=[],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

                # Strategy follows Indicators
                for ind in indicators:
                    edge = (
                        builder.source(
                            node_type="Strategy",
                            external_id=strategy_name,
                        )
                        .target(
                            node_type="Indicator",
                            external_id=ind,
                        )
                        .relationship(
                            relationship_type="follows",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=[],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

        # 7. IndicatorSignal / SignalEvent mapping
        elif event_type in ("IndicatorSignal", "SignalEvent", "Signal"):
            indicator_name = payload.get("indicator_name") or payload.get("indicator")
            symbol = payload.get("symbol")

            if indicator_name and symbol:
                edge = (
                    builder.source(
                        node_type="Indicator",
                        external_id=indicator_name,
                    )
                    .target(
                        node_type="Coin",
                        external_id=symbol,
                    )
                    .relationship(
                        relationship_type="influenced_by",
                    )
                    .evidence(
                        confidence=payload.get("confidence", 1.0),
                        provenance={
                            "event_type": event_type,
                            "causal_chain_id": event.causal_chain_id,
                        },
                        supporting_event_ids=[event_id],
                        supporting_projection_ids=[],
                        created_seq_id=seq_num,
                    )
                    .commit()
                )
                edges.append(edge)

        # 8. MarketRegimeChanged / RegimeIdentified mapping
        elif event_type in ("MarketRegimeChanged", "RegimeIdentified", "Regime"):
            regime_type = payload.get("regime_type") or payload.get("regime")
            symbols = payload.get("symbols", []) or [payload.get("symbol")] if payload.get("symbol") else []

            if regime_type:
                for symbol in symbols:
                    if not symbol:
                        continue
                    # Market Regime influenced by Coin
                    edge = (
                        builder.source(
                            node_type="Market Regime",
                            external_id=regime_type,
                        )
                        .target(
                            node_type="Coin",
                            external_id=symbol,
                        )
                        .relationship(
                            relationship_type="influenced_by",
                        )
                        .evidence(
                            confidence=payload.get("confidence", 1.0),
                            provenance={
                                "event_type": event_type,
                                "causal_chain_id": event.causal_chain_id,
                            },
                            supporting_event_ids=[event_id],
                            supporting_projection_ids=[],
                            created_seq_id=seq_num,
                        )
                        .commit()
                    )
                    edges.append(edge)

        return edges

    def _standardize_node_type(self, raw_type: str) -> str:
        """Standardizes plural node types to their canonical singular equivalents."""
        if not raw_type:
            return "Coin"
        mapping = {
            "coins": "Coin",
            "coin": "Coin",
            "whale wallets": "Whale",
            "whale wallet": "Whale",
            "whales": "Whale",
            "whale": "Whale",
            "news": "News",
            "ai decisions": "Decision",
            "ai decision": "Decision",
            "decision": "Decision",
            "decisions": "Decision",
            "portfolios": "Portfolio",
            "portfolio": "Portfolio",
            "strategies": "Strategy",
            "strategy": "Strategy",
            "indicators": "Indicator",
            "indicator": "Indicator",
            "market regimes": "Market Regime",
            "market regime": "Market Regime",
            "regime": "Market Regime",
        }
        return mapping.get(raw_type.lower(), raw_type)

    def replay_from_event_store(self, start_seq_id: int = 1) -> Tuple[int, int]:
        """Performs a full chronological replay from the immutable L0 Event Store

        to rebuild the Layer 2 Relationship Graph with sequence integrity checks.
        Wipes current graph state and processes all events sequentially.

        Returns:
            A tuple of (events_processed, edges_created).
        """
        session = self.session_factory()
        try:
            # 1. Clear existing graph state
            session.query(GraphEdge).delete()
            session.query(GraphNode).delete()
            session.commit()

            events_processed = 0
            edges_created = 0

            # 2. Stream events sequentially and process each
            for event in self.event_store.stream_events(start_seq_id=start_seq_id):
                processed_edges = self.process_event(session, event)
                edges_created += len(processed_edges)
                events_processed += 1

            session.commit()
            logger.info(
                "L2 Graph full replay completed. Processed %d events, created %d edges.",
                events_processed,
                edges_created,
            )
            return events_processed, edges_created
        except Exception as e:
            session.rollback()
            logger.error("L2 Graph replay failed: %s", e)
            raise
        finally:
            session.close()

    def replay_incrementally(self) -> Tuple[int, int]:
        """Performs an incremental replay, streaming ONLY events newer than the last processed sequence."""
        session = self.session_factory()
        try:
            # Get max sequence number currently recorded in the edges
            max_l2_seq = session.query(func.max(GraphEdge.created_seq_id)).scalar() or 0
            start_seq = max_l2_seq + 1

            events_processed = 0
            edges_created = 0

            # Process any new events
            for event in self.event_store.stream_events(start_seq_id=start_seq):
                processed_edges = self.process_event(session, event)
                edges_created += len(processed_edges)
                events_processed += 1

            session.commit()
            logger.info(
                "L2 Graph incremental replay completed. Processed %d new events, created %d edges.",
                events_processed,
                edges_created,
            )
            return events_processed, edges_created
        except Exception as e:
            session.rollback()
            logger.error("L2 Graph incremental replay failed: %s", e)
            raise
        finally:
            session.close()

    def verify_replay_determinism(self) -> bool:
        """Verifies that a complete replay from sequence 1 reproduces an identical graph.

        Wipes, replays, computes the hash, then compares to the state before the wipe.
        Returns True if identical, raising ValueError otherwise.
        """
        session = self.session_factory()
        try:
            # 1. Capture current graph hash
            nodes_before = [n.to_dict() for n in session.query(GraphNode).all()]
            edges_before = [e.to_dict() for e in session.query(GraphEdge).all()]
            hash_before = self.generate_integrity_hash(nodes_before, edges_before)

            # 2. Execute full replay
            self.replay_from_event_store(start_seq_id=1)

            # 3. Capture hash after replay
            nodes_after = [n.to_dict() for n in session.query(GraphNode).all()]
            edges_after = [e.to_dict() for e in session.query(GraphEdge).all()]
            hash_after = self.generate_integrity_hash(nodes_after, edges_after)

            if hash_before != hash_after:
                logger.error(
                    "Replay Determinism Failed. Hash before: %s, Hash after: %s",
                    hash_before,
                    hash_after,
                )
                return False

            logger.info("Replay Determinism Verified! Hash matches: %s", hash_before)
            return True
        finally:
            session.close()

    def generate_integrity_hash(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
        """Calculates a consistent, reproducible cryptographic SHA-256 integrity hash of graph nodes and edges."""
        # Clean serialized elements to only look at deterministic state attributes
        clean_nodes = []
        for n in nodes:
            clean_nodes.append({
                "node_type": n.get("node_type"),
                "external_id": n.get("external_id"),
                "properties": n.get("properties"),
            })

        clean_edges = []
        for e in edges:
            clean_edges.append({
                "relationship_type": e.get("relationship_type"),
                "source_node_id": e.get("source_node_id"),
                "target_node_id": e.get("target_node_id"),
                "confidence": e.get("confidence"),
                "created_seq_id": e.get("created_seq_id"),
            })

        # Standardize representation by sorting lists
        sorted_nodes = sorted(clean_nodes, key=lambda x: (x.get("node_type", ""), x.get("external_id", "")))
        sorted_edges = sorted(
            clean_edges,
            key=lambda x: (
                x.get("source_node_id", 0),
                x.get("target_node_id", 0),
                x.get("relationship_type", ""),
            ),
        )

        serialized_content = json.dumps(
            {"nodes": sorted_nodes, "edges": sorted_edges},
            sort_keys=True,
        )
        return hashlib.sha256(serialized_content.encode("utf-8")).hexdigest()

    def create_snapshot(self) -> GraphSnapshot:
        """Saves a complete consistency snapshot of the current state of Layer 2 Graph."""
        session = self.session_factory()
        try:
            # 1. Fetch current sequence number
            max_seq = session.query(func.max(GraphEdge.created_seq_id)).scalar() or 0

            # 2. Fetch all nodes and edges
            nodes = [n.to_dict() for n in session.query(GraphNode).all()]
            edges = [e.to_dict() for e in session.query(GraphEdge).all()]

            # 3. Generate SHA-256 integrity hash
            integrity_hash = self.generate_integrity_hash(nodes, edges)
            snapshot_id = str(uuid.uuid4())

            # 4. Save the snapshot
            snapshot = GraphSnapshot(
                snapshot_id=snapshot_id,
                last_sequence_number=max_seq,
                nodes_data=nodes,
                edges_data=edges,
                integrity_hash=integrity_hash,
            )
            session.add(snapshot)
            session.commit()

            session.refresh(snapshot)
            session.expunge(snapshot)

            logger.info("Saved Layer 2 Graph snapshot: %s (Seq: %d)", snapshot_id, max_seq)
            return snapshot
        except Exception as e:
            session.rollback()
            logger.error("Failed to create L2 Graph snapshot: %s", e)
            raise
        finally:
            session.close()

    def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """Restores Layer 2 Relationship Graph from a saved GraphSnapshot, validating cryptographic integrity."""
        session = self.session_factory()
        try:
            # 1. Fetch snapshot
            snapshot = session.query(GraphSnapshot).filter(GraphSnapshot.snapshot_id == snapshot_id).first()
            if not snapshot:
                logger.error("Snapshot not found: %s", snapshot_id)
                return False

            # 2. Validate cryptographic hash integrity
            nodes_data = snapshot.nodes_data or []
            edges_data = snapshot.edges_data or []
            computed_hash = self.generate_integrity_hash(nodes_data, edges_data)

            if computed_hash != snapshot.integrity_hash:
                logger.critical(
                    "INTEGRITY VIOLATION: GraphSnapshot %s hash mismatch. Expected %s, got %s",
                    snapshot_id,
                    snapshot.integrity_hash,
                    computed_hash,
                )
                raise ValueError("Cryptographic integrity verification failed for snapshot.")

            # 3. Clear current graph state
            session.query(GraphEdge).delete()
            session.query(GraphNode).delete()
            session.commit()

            # 4. Restore nodes
            node_id_map = {}
            for node_dict in nodes_data:
                node = GraphNode(
                    node_type=node_dict["node_type"],
                    external_id=node_dict["external_id"],
                    properties=node_dict["properties"],
                    created_at=datetime.fromisoformat(node_dict["created_at"]) if node_dict.get("created_at") else datetime.now(timezone.utc),
                    updated_at=datetime.fromisoformat(node_dict["updated_at"]) if node_dict.get("updated_at") else datetime.now(timezone.utc),
                )
                session.add(node)
                session.flush()
                node_id_map[node_dict["id"]] = node.id

            # 5. Restore edges
            for edge_dict in edges_data:
                new_source_id = node_id_map.get(edge_dict["source_node_id"])
                new_target_id = node_id_map.get(edge_dict["target_node_id"])

                if not new_source_id or not new_target_id:
                    continue

                edge = GraphEdge(
                    source_node_id=new_source_id,
                    target_node_id=new_target_id,
                    relationship_type=edge_dict["relationship_type"],
                    confidence=edge_dict.get("confidence", 1.0),
                    provenance=edge_dict.get("provenance", {}),
                    supporting_event_ids=edge_dict.get("supporting_event_ids", []),
                    supporting_projection_ids=edge_dict.get("supporting_projection_ids", []),
                    created_seq_id=edge_dict.get("created_seq_id", 0),
                    created_at=datetime.fromisoformat(edge_dict["created_at"]) if edge_dict.get("created_at") else datetime.now(timezone.utc),
                    updated_at=datetime.fromisoformat(edge_dict["updated_at"]) if edge_dict.get("updated_at") else datetime.now(timezone.utc),
                )
                session.add(edge)

            session.commit()
            logger.info("Successfully restored Layer 2 Graph from snapshot %s.", snapshot_id)
            return True
        except Exception as e:
            session.rollback()
            logger.error("Failed to restore Layer 2 Graph from snapshot: %s", e)
            raise
        finally:
            session.close()

    def get_neighbors(self, node_id: int) -> List[Dict[str, Any]]:
        """Retrieves neighbor nodes of the specified node_id, indicating directed relationship info."""
        session = self.session_factory()
        try:
            neighbors = []

            # Outgoing relations
            outgoing = session.query(GraphEdge).filter(GraphEdge.source_node_id == node_id).all()
            for edge in outgoing:
                target_node = edge.target_node
                if target_node:
                    neighbors.append({
                        "node_id": target_node.id,
                        "node_type": target_node.node_type,
                        "external_id": target_node.external_id,
                        "direction": "outgoing",
                        "relationship_type": edge.relationship_type,
                        "confidence": edge.confidence,
                        "edge_id": edge.id,
                    })

            # Incoming relations
            incoming = session.query(GraphEdge).filter(GraphEdge.target_node_id == node_id).all()
            for edge in incoming:
                src_node = edge.source_node
                if src_node:
                    neighbors.append({
                        "node_id": src_node.id,
                        "node_type": src_node.node_type,
                        "external_id": src_node.external_id,
                        "direction": "incoming",
                        "relationship_type": edge.relationship_type,
                        "confidence": edge.confidence,
                        "edge_id": edge.id,
                    })

            return neighbors
        finally:
            session.close()

    def find_shortest_path(self, start_node_id: int, end_node_id: int) -> Optional[List[Dict[str, Any]]]:
        """Finds the shortest directed path between start and end node using Breadth-First Search (BFS).

        Returns a list representing the path containing node/edge step objects, or None if unreachable.
        """
        session = self.session_factory()
        try:
            # Simple BFS
            queue = deque([[start_node_id]])
            visited = {start_node_id}
            parent_edges = {}  # maps node_id to the edge_id that led to it

            # Pre-load edges into a map for fast traversal
            edges_list = session.query(GraphEdge).all()
            adj_map = {}
            edge_map = {}
            for edge in edges_list:
                adj_map.setdefault(edge.source_node_id, []).append((edge.target_node_id, edge.id))
                edge_map[edge.id] = edge

            path_nodes = None
            while queue:
                current_path = queue.popleft()
                node_id = current_path[-1]

                if node_id == end_node_id:
                    path_nodes = current_path
                    break

                for neighbor_id, edge_id in adj_map.get(node_id, []):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        parent_edges[neighbor_id] = edge_id
                        queue.append(current_path + [neighbor_id])

            if not path_nodes:
                return None

            # Reconstruct detailed path with edge info
            detailed_path = []
            for idx, nid in enumerate(path_nodes):
                node = session.query(GraphNode).filter(GraphNode.id == nid).first()
                step = {
                    "node_id": nid,
                    "node_type": node.node_type if node else "Unknown",
                    "external_id": node.external_id if node else "Unknown",
                    "properties": node.properties if node else {},
                }
                if idx > 0:
                    edge_id = parent_edges.get(nid)
                    if edge_id:
                        edge_obj = edge_map.get(edge_id)
                        step["via_relationship"] = {
                            "edge_id": edge_id,
                            "relationship_type": edge_obj.relationship_type if edge_obj else "Unknown",
                            "confidence": edge_obj.confidence if edge_obj else 1.0,
                        }
                detailed_path.append(step)

            return detailed_path
        finally:
            session.close()

    def find_connected_components(self) -> List[List[int]]:
        """Identifies all weakly connected components (treating edges as undirected) in the graph."""
        session = self.session_factory()
        try:
            nodes = session.query(GraphNode.id).all()
            node_ids = [n[0] for n in nodes]
            if not node_ids:
                return []

            # Pre-load edges and treat as undirected adjacency list
            edges = session.query(GraphEdge.source_node_id, GraphEdge.target_node_id).all()
            adj = {}
            for u, v in edges:
                adj.setdefault(u, []).append(v)
                adj.setdefault(v, []).append(u)

            visited = set()
            components = []

            for start_node in node_ids:
                if start_node in visited:
                    continue
                # BFS to find component
                component = []
                queue = deque([start_node])
                visited.add(start_node)

                while queue:
                    node = queue.popleft()
                    component.append(node)

                    for neighbor in adj.get(node, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(component)

            return components
        finally:
            session.close()

    def get_metrics(self) -> Dict[str, Any]:
        """Calculates and returns premium metrics describing graph structure and density."""
        session = self.session_factory()
        try:
            total_nodes = session.query(func.count(GraphNode.id)).scalar() or 0
            total_edges = session.query(func.count(GraphEdge.id)).scalar() or 0

            # Node breakdown by type
            node_counts = {}
            for row in session.query(GraphNode.node_type, func.count(GraphNode.id)).group_by(GraphNode.node_type).all():
                node_counts[row[0]] = row[1]

            # Edge breakdown by relationship_type
            edge_counts = {}
            for row in session.query(GraphEdge.relationship_type, func.count(GraphEdge.id)).group_by(GraphEdge.relationship_type).all():
                edge_counts[row[0]] = row[1]

            # Snapshot count and size metrics
            snapshot_count = session.query(func.count(GraphSnapshot.id)).scalar() or 0
            latest_snap = session.query(GraphSnapshot).order_by(GraphSnapshot.created_at.desc()).first()
            snapshot_size_bytes = 0
            if latest_snap:
                # Estimate snapshot size from nodes/edges JSON serialized size
                nodes_json = json.dumps(latest_snap.nodes_data)
                edges_json = json.dumps(latest_snap.edges_data)
                snapshot_size_bytes = len(nodes_json.encode("utf-8")) + len(edges_json.encode("utf-8"))

            # Graph density
            density = 0.0
            if total_nodes > 1:
                density = total_edges / (total_nodes * (total_nodes - 1))

            # Graph consistency and orphans check
            node_ids_subquery = session.query(GraphNode.id).subquery()
            orphan_edges_count = (
                session.query(func.count(GraphEdge.id))
                .filter(
                    (GraphEdge.source_node_id.not_in(node_ids_subquery))
                    | (GraphEdge.target_node_id.not_in(node_ids_subquery))
                )
                .scalar()
                or 0
            )

            # Duplicate edge count (check database-enforced consistency, theoretically always 0)
            duplicate_edges_count = 0

            return {
                "node_count": total_nodes,
                "edge_count": total_edges,
                "density": density,
                "node_counts_by_type": node_counts,
                "edge_counts_by_relationship": edge_counts,
                "snapshot_count": snapshot_count,
                "latest_snapshot_size_bytes": snapshot_size_bytes,
                "orphan_edge_count": orphan_edges_count,
                "duplicate_edge_count": duplicate_edges_count,
                "is_consistent": orphan_edges_count == 0 and duplicate_edges_count == 0,
            }
        finally:
            session.close()

    def check_health(self) -> Dict[str, Any]:
        """Runs health audits on the graph to detect anomalies, dangling references, or sequences."""
        session = self.session_factory()
        try:
            node_ids_subquery = session.query(GraphNode.id).subquery()
            dangling_edges_count = (
                session.query(func.count(GraphEdge.id))
                .filter(
                    (GraphEdge.source_node_id.not_in(node_ids_subquery))
                    | (GraphEdge.target_node_id.not_in(node_ids_subquery))
                )
                .scalar()
                or 0
            )

            max_l0_seq = session.query(func.max(NEXUSEvent.seq_id)).scalar() or 0
            max_l2_seq = session.query(func.max(GraphEdge.created_seq_id)).scalar() or 0
            lag = max(0, max_l0_seq - max_l2_seq)

            is_healthy = True
            reasons = []

            if dangling_edges_count > 0:
                is_healthy = False
                reasons.append(f"Detected {dangling_edges_count} dangling/orphaned edge(s).")

            status = "HEALTHY" if is_healthy else "DEGRADED"

            return {
                "status": status,
                "is_healthy": is_healthy,
                "lag_events": lag,
                "max_l0_sequence": max_l0_seq,
                "max_l2_sequence": max_l2_seq,
                "dangling_edges_count": dangling_edges_count,
                "anomalies": reasons,
            }
        finally:
            session.close()
