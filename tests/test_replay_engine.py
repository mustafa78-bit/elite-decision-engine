from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from database import Signal, Trade
from decision.replay import ReplayEngine


class TestReplayEngine:

    def setup_method(self):
        self.engine = ReplayEngine()

    def test_initialization(self):
        assert self.engine.consensus_engine is not None
        assert self.engine.evidence_engine is not None
        assert self.engine.explanation_service is not None
        assert len(self.engine.consensus_engine.agents) >= 6

    @patch("decision.replay.get_session")
    def test_get_signal_context(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_signal = Signal(
            id=42,
            symbol="ETHUSDT",
            side="SHORT",
            timeframe="1h",
            price=3000.0,
            score=0.7,
            confidence=75.0,
            volume_score=0.6,
            btc_health=0.5,
            trend_score=0.8,
            risk_score=0.2,
            funding_score=0.1,
            oi_score=0.2,
            cvd_score=0.3,
            status="APPROVED",
        )

        mock_trade = Trade(
            pnl=12.5,
            status="CLOSED",
        )

        # Mock the session queries
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_signal, mock_trade]

        ctx = self.engine.get_signal_context(42)

        assert ctx["signal_id"] == 42
        assert ctx["symbol"] == "ETHUSDT"
        assert ctx["side"] == "SHORT"
        assert ctx["price"] == 3000.0
        assert ctx["trade_pnl"] == 12.5
        assert ctx["trade_status"] == "CLOSED"

    @patch("decision.replay.get_session")
    def test_replay_signal_no_mods(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_signal = Signal(
            id=101,
            symbol="BTCUSDT",
            side="LONG",
            timeframe="4h",
            price=50000.0,
            score=0.8,
            confidence=80.0,
            volume_score=0.7,
            btc_health=0.8,
            trend_score=0.85,
            risk_score=0.1,
            funding_score=0.2,
            oi_score=0.3,
            cvd_score=0.4,
            status="APPROVED",
        )

        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_signal, None]

        # Execute replay
        res = self.engine.replay_signal(101)

        assert res["original_context"]["symbol"] == "BTCUSDT"
        assert res["replayed_context"]["symbol"] == "BTCUSDT"
        assert res["modifications"] == {}
        assert "council_report" in res
        assert "evidence_report" in res
        assert "explanation" in res

    @patch("decision.replay.get_session")
    def test_replay_signal_with_modifications(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_signal = Signal(
            id=202,
            symbol="SOLUSDT",
            side="LONG",
            timeframe="1h",
            price=100.0,
            score=0.6,
            confidence=60.0,
            volume_score=0.5,
            btc_health=0.4,
            trend_score=0.5,
            risk_score=0.3,
            funding_score=0.1,
            oi_score=0.2,
            cvd_score=0.3,
            status="WATCH",
        )

        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_signal, None]

        # Apply high risk override
        mods = {"risk_score": 0.95, "trend_score": 0.1}
        res = self.engine.replay_signal(202, modifications=mods)

        assert res["original_context"]["risk_score"] == 0.3
        assert res["replayed_context"]["risk_score"] == 0.95
        assert res["replayed_context"]["trend_score"] == 0.1
        assert res["modifications"] == mods
