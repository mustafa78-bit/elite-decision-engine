import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from database import get_session
from memory.l0_event_log.service import L0EventStore
from memory.l0_event_log.models import NEXUSEvent
from memory.l2_graph.models import GraphNode, GraphEdge, GraphSnapshot
from memory.l2_graph.engine import GraphEngine
from memory.l2_graph.registry import NodeRegistry, EdgeRegistry
from memory.l2_graph.builder import RelationshipBuilder


@pytest.fixture
def graph_setup(session_factory, monkeypatch):
    """Sets up the L2 Relationship Graph engine and store dynamically patched for isolated testing."""
    monkeypatch.setattr("memory.l0_event_log.service.get_session", session_factory)
    monkeypatch.setattr("api.routes.nexus_l2_graph.get_session", session_factory)

    store = L0EventStore(session_factory=session_factory)
    engine = GraphEngine(session_factory=session_factory, event_store=store)

    return store, engine, session_factory


def test_node_registry_idempotency_and_merge(graph_setup):
    """Verifies that NodeRegistry gets or creates nodes idempotently and merges properties monotonically."""
    store, engine, session_factory = graph_setup
    session = session_factory()

    try:
        # Create a new Coin node
        node1 = NodeRegistry.get_or_create_node(
            session, node_type="Coin", external_id="BTC", properties={"price": 60000.0}
        )
        assert node1.id is not None
        assert node1.node_type == "Coin"
        assert node1.properties == {"price": 60000.0}

        # Retrieve/create again - should return same node and merge new properties
        node2 = NodeRegistry.get_or_create_node(
            session, node_type="Coin", external_id="BTC", properties={"volume_24h": 1.2e9, "price": 61000.0}
        )
        assert node1.id == node2.id
        assert node2.properties == {"price": 61000.0, "volume_24h": 1.2e9}

        # Verify list_nodes
        nodes = NodeRegistry.list_nodes(session, node_type="Coin")
        assert len(nodes) == 1
        assert nodes[0].external_id == "BTC"
    finally:
        session.close()


def test_edge_registry_monotonic_sequence_and_evidence(graph_setup):
    """Ensures that EdgeRegistry updates edge properties monotonically based on sequence order,

    validates evidence existence, and prevents duplicate edges.
    """
    store, engine, session_factory = graph_setup
    session = session_factory()

    try:
        n1 = NodeRegistry.get_or_create_node(session, "Whale", "wallet_abc")
        n2 = NodeRegistry.get_or_create_node(session, "Coin", "SOL")

        # 1. Validation check: edges must never exist without evidence (raising ValueError)
        with pytest.raises(ValueError, match="without evidence"):
            EdgeRegistry.get_or_create_edge(
                session,
                source_node_id=n1.id,
                target_node_id=n2.id,
                relationship_type="traded",
                supporting_event_ids=[],
                supporting_projection_ids=[],
            )

        # 2. Create edge with valid evidence
        edge1 = EdgeRegistry.get_or_create_edge(
            session,
            source_node_id=n1.id,
            target_node_id=n2.id,
            relationship_type="traded",
            confidence=0.8,
            provenance={"source": "test"},
            supporting_event_ids=["evt-1"],
            supporting_projection_ids=["WhaleView"],
            created_seq_id=10,
        )
        assert edge1.id is not None
        assert edge1.confidence == 0.8
        assert edge1.supporting_event_ids == ["evt-1"]
        assert edge1.supporting_projection_ids == ["WhaleView"]
        assert edge1.created_seq_id == 10

        # 3. Process stale out-of-order update (sequence_number < edge.created_seq_id)
        # Should ignore metadata updates but accumulate unique evidence list!
        edge2 = EdgeRegistry.get_or_create_edge(
            session,
            source_node_id=n1.id,
            target_node_id=n2.id,
            relationship_type="traded",
            confidence=0.5,  # lower confidence, should be ignored
            provenance={"source": "stale"},
            supporting_event_ids=["evt-0"],
            supporting_projection_ids=["NewsView"],
            created_seq_id=5,
        )
        assert edge1.id == edge2.id
        assert edge2.confidence == 0.8  # retained
        assert edge2.created_seq_id == 10  # retained
        assert "evt-0" in edge2.supporting_event_ids  # unique evidence accumulated
        assert "evt-1" in edge2.supporting_event_ids
        assert "NewsView" in edge2.supporting_projection_ids

        # 4. Process newer/fresher update (sequence_number >= edge.created_seq_id)
        # Should overwrite metadata and accumulate evidence
        edge3 = EdgeRegistry.get_or_create_edge(
            session,
            source_node_id=n1.id,
            target_node_id=n2.id,
            relationship_type="traded",
            confidence=0.95,
            provenance={"source": "new"},
            supporting_event_ids=["evt-2"],
            supporting_projection_ids=["WhaleView"],
            created_seq_id=15,
        )
        assert edge3.confidence == 0.95
        assert edge3.created_seq_id == 15
        assert "evt-2" in edge3.supporting_event_ids
        assert len(edge3.supporting_event_ids) == 3  # evt-0, evt-1, evt-2
    finally:
        session.close()


def test_fluent_relationship_builder(graph_setup):
    """Verifies that RelationshipBuilder provides an elegant fluent builder pattern with proper commit hooks."""
    store, engine, session_factory = graph_setup
    session = session_factory()

    try:
        builder = RelationshipBuilder(session)
        edge = (
            builder.source("Strategy", "MomentumBuiltin", {"pnl": 0.05})
            .target("Portfolio", "MainAlpha")
            .relationship("belongs_to")
            .evidence(
                confidence=1.0,
                provenance={"system": "StrategyLab"},
                supporting_event_ids=["evt-strat-1"],
                created_seq_id=2,
            )
            .commit()
        )

        assert edge.id is not None
        assert edge.relationship_type == "belongs_to"
        assert edge.confidence == 1.0
        assert edge.source_node.node_type == "Strategy"
        assert edge.target_node.node_type == "Portfolio"
    finally:
        session.close()


def test_deterministic_replay_and_graph_identicalness(graph_setup):
    """Tests full and incremental event replays, ensuring deterministic rebuilding

    of identical graphs and sequence checks.
    """
    store, engine, session_factory = graph_setup
    actor = {"id": "test-actor", "type": "SYSTEM", "name": "Test Actor"}

    # 1. Append structured events to L0 store
    evt1 = store.append(
        "WhaleActivity",
        {"whale_id": "whale_0x1", "symbol": "BTC", "action": "accumulate", "amount": 100.0},
        actor,
        "chain-1",
    )
    evt2 = store.append(
        "NewsPublished",
        {"news_id": "news_99", "headline": "Whale transfers BTC", "symbols": ["BTC"], "wallets": ["whale_0x1"]},
        actor,
        "chain-1",
    )
    evt3 = store.append(
        "AIDecision",
        {
            "decision_id": "dec-101",
            "symbol": "BTC",
            "predicted_side": "BUY",
            "confidence": 0.88,
            "strategy": "MeanReverting",
            "portfolio": "PortfolioMaster",
            "indicators": [{"name": "RSI", "confirmed": True}, {"name": "MACD", "confirmed": False}],
        },
        actor,
        "chain-2",
    )

    # 2. Perform full replay
    processed_count, created_edges = engine.replay_from_event_store()
    assert processed_count == 3
    assert created_edges > 0

    session = session_factory()
    try:
        # Check node types mapped (should be singular)
        nodes = session.query(GraphNode).all()
        node_types = {n.node_type for n in nodes}
        assert "Whale" in node_types
        assert "Coin" in node_types
        assert "News" in node_types
        assert "Decision" in node_types
        assert "Strategy" in node_types
        assert "Portfolio" in node_types
        assert "Indicator" in node_types

        # Check edge counts
        edges = session.query(GraphEdge).all()
        assert len(edges) > 0

        # Compute initial consistency hash
        nodes_dict = [n.to_dict() for n in nodes]
        edges_dict = [e.to_dict() for e in edges]
        initial_hash = engine.generate_integrity_hash(nodes_dict, edges_dict)

        # 3. Verify determinism: replay again and verify hash identicalness
        assert engine.verify_replay_determinism() is True

        # 4. Incremental Replay Test: Append more events and replay incrementally
        evt4 = store.append(
            "PortfolioUpdated",
            {"portfolio_id": "PortfolioMaster", "symbol": "BTC", "side": "BUY", "quantity": 10.0},
            actor,
            "chain-2",
        )

        inc_processed, inc_edges = engine.replay_incrementally()
        assert inc_processed == 1
        assert inc_edges >= 1

        # Check that new edges were created
        edges_now = session.query(GraphEdge).all()
        assert len(edges_now) > len(edges)
    finally:
        session.close()


def test_cryptographic_snapshot_and_restoration(graph_setup):
    """Validates L2 graph consistency snapshots, hash verification, and successful rollback recovery."""
    store, engine, session_factory = graph_setup
    actor = {"id": "test-actor", "type": "SYSTEM", "name": "Test Actor"}

    # Seed events
    store.append(
        "WhaleActivity",
        {"whale_id": "whale_0x2", "symbol": "ETH", "action": "distribute"},
        actor,
        "chain-snap",
    )

    # Replay
    engine.replay_from_event_store()

    session = session_factory()
    try:
        nodes_count_before = session.query(GraphNode).count()
        edges_count_before = session.query(GraphEdge).count()
        assert nodes_count_before > 0

        # 1. Create snapshot
        snapshot = engine.create_snapshot()
        assert snapshot.snapshot_id is not None
        assert snapshot.integrity_hash is not None

        # 2. Modify graph manually in session to corrupt/change it
        NodeRegistry.get_or_create_node(session, "Coin", "SOL")
        session.commit()
        assert session.query(GraphNode).count() == nodes_count_before + 1

        # 3. Restore from snapshot - should revert to original state
        success = engine.restore_from_snapshot(snapshot.snapshot_id)
        assert success is True
        assert session.query(GraphNode).count() == nodes_count_before
        assert session.query(GraphEdge).count() == edges_count_before

        # 4. Corrupt snapshot integrity hash manually and assert restore failure
        snap_record = session.query(GraphSnapshot).filter(GraphSnapshot.snapshot_id == snapshot.snapshot_id).first()
        snap_record.integrity_hash = "corrupted_hash"
        session.commit()

        with pytest.raises(ValueError, match="integrity verification failed"):
            engine.restore_from_snapshot(snapshot.snapshot_id)
    finally:
        session.close()


def test_graph_query_capabilities(graph_setup):
    """Audits BFS shortest path, directed neighbors lookup, and connected components."""
    store, engine, session_factory = graph_setup
    session = session_factory()

    try:
        # Build manual chain for testing paths
        # A (Coin:BTC) -> B (Decision:dec1) -> C (Strategy:strat1) -> D (Portfolio:port1)
        n_a = NodeRegistry.get_or_create_node(session, "Coin", "BTC")
        n_b = NodeRegistry.get_or_create_node(session, "Decision", "dec1")
        n_c = NodeRegistry.get_or_create_node(session, "Strategy", "strat1")
        n_d = NodeRegistry.get_or_create_node(session, "Portfolio", "port1")

        EdgeRegistry.get_or_create_edge(
            session, n_a.id, n_b.id, "mentions", confidence=0.9, supporting_event_ids=["evt-1"], created_seq_id=1
        )
        EdgeRegistry.get_or_create_edge(
            session, n_b.id, n_c.id, "generated", confidence=1.0, supporting_event_ids=["evt-2"], created_seq_id=2
        )
        EdgeRegistry.get_or_create_edge(
            session, n_c.id, n_d.id, "belongs_to", confidence=1.0, supporting_event_ids=["evt-3"], created_seq_id=3
        )

        session.commit()

        # 1. Neighbor Lookup
        neighbors = engine.get_neighbors(n_b.id)
        assert len(neighbors) == 2
        directions = {n["direction"] for n in neighbors}
        assert "incoming" in directions  # from BTC
        assert "outgoing" in directions  # to strat1

        # 2. Shortest Path Validation (BTC to port1)
        path = engine.find_shortest_path(n_a.id, n_d.id)
        assert path is not None
        assert len(path) == 4
        assert path[0]["node_id"] == n_a.id
        assert path[-1]["node_id"] == n_d.id
        assert "via_relationship" in path[1]
        assert path[1]["via_relationship"]["relationship_type"] == "mentions"

        # Path to unreachable node
        n_unreachable = NodeRegistry.get_or_create_node(session, "Coin", "ADA")
        session.commit()
        unreachable_path = engine.find_shortest_path(n_a.id, n_unreachable.id)
        assert unreachable_path is None

        # 3. Connected Components
        components = engine.find_connected_components()
        assert len(components) == 2  # {A, B, C, D} and {ADA}
        comp_sizes = {len(c) for c in components}
        assert 4 in comp_sizes
        assert 1 in comp_sizes
    finally:
        session.close()


def test_metrics_and_health_audits(graph_setup):
    """Tests the coverage of graph density, orphan edge counts, and health synchronization lag check."""
    store, engine, session_factory = graph_setup
    session = session_factory()

    try:
        n_a = NodeRegistry.get_or_create_node(session, "Coin", "BTC")
        n_b = NodeRegistry.get_or_create_node(session, "Decision", "dec2")

        EdgeRegistry.get_or_create_edge(
            session, n_a.id, n_b.id, "mentions", confidence=0.8, supporting_event_ids=["evt-1"], created_seq_id=1
        )
        session.commit()

        # Get metrics
        metrics = engine.get_metrics()
        assert metrics["node_count"] == 2
        assert metrics["edge_count"] == 1
        assert metrics["is_consistent"] is True

        # Check health
        health = engine.check_health()
        assert health["status"] == "HEALTHY"
        assert health["is_healthy"] is True
        assert health["dangling_edges_count"] == 0
    finally:
        session.close()


def test_fastapi_graph_endpoints_e2e(api_client, graph_setup):
    """E2E Integration test verifying all generic FastAPI endpoints under the /graph prefix."""
    store, engine, session_factory = graph_setup

    # Override FastAPI dependency registry to point to our test SQLite session
    from api.main import app

    # Locate the original, unpatched get_session from FastAPI route dependants
    # including nested _IncludedRouter original routers
    for route in app.routes:
        routes_to_check = []
        if type(route).__name__ == "_IncludedRouter":
            routes_to_check = route.original_router.routes
        else:
            routes_to_check = [route]

        for r in routes_to_check:
            if hasattr(r, "dependant") and r.dependant:
                for dep in r.dependant.dependencies:
                    if dep.call and getattr(dep.call, "__name__", None) == "get_session":
                        app.dependency_overrides[dep.call] = session_factory

    actor = {"id": "api-actor", "type": "SYSTEM", "name": "API Actor"}

    # Seed an event
    store.append(
        "WhaleActivity",
        {"whale_id": "wallet_xyz", "symbol": "BTC", "action": "accumulate"},
        actor,
        "chain-api",
    )

    # 1. Trigger Replay API
    res = api_client.post("/graph/replay")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["events_processed"] == 1

    # 2. Get Nodes list
    res = api_client.get("/graph/nodes")
    assert res.status_code == 200
    nodes = res.json()
    assert len(nodes) == 2
    node_types = {n["node_type"] for n in nodes}
    assert "Whale" in node_types
    assert "Coin" in node_types

    # Find whale node ID
    whale_node = next(n for n in nodes if n["node_type"] == "Whale")
    coin_node = next(n for n in nodes if n["node_type"] == "Coin")

    # 3. Get Single Node
    res = api_client.get(f"/graph/node/{whale_node['id']}")
    assert res.status_code == 200
    assert res.json()["external_id"] == "wallet_xyz"

    # Get non-existing node
    res = api_client.get("/graph/node/99999")
    assert res.status_code == 404

    # 4. Get Edges
    res = api_client.get("/graph/edges")
    assert res.status_code == 200
    edges = res.json()
    assert len(edges) == 1
    assert edges[0]["relationship_type"] == "accumulated"

    # 5. Get Neighbors
    res = api_client.get(f"/graph/neighbors/{whale_node['id']}")
    assert res.status_code == 200
    neighbors = res.json()
    assert len(neighbors) == 1
    assert neighbors[0]["node_id"] == coin_node["id"]

    # 6. Find Path
    res = api_client.get(f"/graph/path?start_node_id={whale_node['id']}&end_node_id={coin_node['id']}")
    assert res.status_code == 200
    path = res.json()
    assert len(path) == 2

    # 7. Get Metrics & Health
    res = api_client.get("/graph/metrics")
    assert res.status_code == 200
    assert res.json()["node_count"] == 2

    res = api_client.get("/graph/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

    # 8. Snapshot creation
    res = api_client.post("/graph/snapshot")
    assert res.status_code == 201
    snap_data = res.json()
    assert snap_data["status"] == "success"
    snap_id = snap_data["snapshot_id"]

    # 9. Restore snapshot
    res = api_client.post(f"/graph/snapshot/restore?snapshot_id={snap_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
