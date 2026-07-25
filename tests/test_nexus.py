import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from database import Signal, Trade, get_session
from services.nexus_service import NexusService


class TestNexusServiceUnit:

    @pytest.mark.asyncio
    async def test_nexus_orchestration_all_online(self):
        """Test that NexusService aggregates all 9 subsystems successfully when they are online."""
        svc = NexusService()

        # Simple concurrent aggregate execution
        report = await svc.get_nexus_summary(symbol="BTC")

        assert report["symbol"] == "BTC"
        assert "timestamp" in report
        assert "availability" in report
        assert "orchestrated_data" in report

        # Verify 7 required dimensions are explained
        orchestrated = report["orchestrated_data"]
        for dim in ["why", "why_now", "risk", "confidence", "supporting_evidence", "invalidation", "final_recommendation"]:
            assert dim in orchestrated

        # Check evidence first parameters (source, confidence, timestamp)
        for evidence in orchestrated["supporting_evidence"]:
            assert "source" in evidence
            assert "confidence" in evidence
            assert "timestamp" in evidence

    @pytest.mark.asyncio
    async def test_nexus_graceful_degradation_partial_offline(self):
        """Test that NexusService gracefully degrades and never crashes if a subset of services are offline."""
        svc = NexusService()

        # Mock explanation service to raise exception (representing offline)
        with patch.object(svc.explanation_service, "explain_signal", side_effect=Exception("Timeout Connection Closed")):
            report = await svc.get_nexus_summary(symbol="BTC")

            assert report["symbol"] == "BTC"
            # Subsystem marked as OFFLINE
            assert report["availability"]["explanation"] == "OFFLINE"
            # Entire response is still assembled successfully without raising error
            assert report["orchestrated_data"]["why"]["explanation"] is not None


class TestNexusIntegration:

    def test_nexus_overview_endpoint(self, api_client):
        """Integration test for GET /nexus/overview."""
        resp = api_client.get("/nexus/overview?symbol=BTC")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "BTC"
        assert "availability" in body
        assert "orchestrated_data" in body

    def test_nexus_briefing_endpoint(self, api_client):
        """Integration test for GET /nexus/briefing."""
        resp = api_client.get("/nexus/briefing?symbol=ETH")
        assert resp.status_code == 200
        body = resp.json()
        assert "title" in body
        assert "market_summary" in body
        assert "tactical_triggers" in body
        assert "risk_assessment" in body
        assert "recommendation_summary" in body

    def test_nexus_mission_endpoint(self, api_client):
        """Integration test for GET /nexus/mission."""
        resp = api_client.get("/nexus/mission?symbol=SOL")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "SOL"
        assert "subsystem_readiness" in body
        assert "targets" in body
        assert "invalidation_parameters" in body

    def test_nexus_query_endpoint(self, api_client):
        """Integration test for POST /nexus/query."""
        payload = {
            "symbol": "BTC",
            "timeframe": "4h",
            "side": "SHORT"
        }
        resp = api_client.post("/nexus/query", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"]["symbol"] == "BTC"
        assert body["query"]["timeframe"] == "4h"
        assert "orchestrated_data" in body

    def test_nexus_explain_signal_endpoint(self, api_client, db_session):
        """Integration test for GET /nexus/explain/{signal_id}."""
        # Seed a test signal
        sig = Signal(
            symbol="BTC",
            side="LONG",
            timeframe="1h",
            price=60000.0,
            status="OPEN"
        )
        db_session.add(sig)
        db_session.commit()
        db_session.refresh(sig)

        resp = api_client.get(f"/nexus/explain/{sig.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["signal_id"] == sig.id
        assert "orchestrated_data" in body
        assert "availability" in body

    def test_nexus_explain_signal_not_found(self, api_client):
        """Integration test for GET /nexus/explain/{signal_id} with non-existent ID."""
        resp = api_client.get("/nexus/explain/99999")
        assert resp.status_code == 404
