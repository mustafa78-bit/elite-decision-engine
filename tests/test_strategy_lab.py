import pytest
import logging
# Suppress httpx2 logging formatting bug in library mock clients
logging.getLogger("httpx2").setLevel(logging.WARNING)

from datetime import datetime, timezone, timedelta
from database import Signal, SavedStrategy, Trade
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def seed_signals(db_session):
    """Seed signals for strategy lab testing."""
    now = datetime.now(timezone.utc)
    # Seed 10 signals
    sigs = []
    for i in range(10):
        sig = Signal(
            symbol="BTC" if i % 2 == 0 else "ETH",
            side="LONG" if i % 3 != 0 else "SHORT",
            timeframe="1h" if i % 2 == 0 else "15m",
            price=60000.0 if i % 2 == 0 else 3000.0,
            trend_score=0.9 if i % 2 == 0 else 0.3,
            volume_score=0.8,
            funding_score=0.7,
            oi_score=0.6,
            cvd_score=0.75,
            risk_score=0.8,
            market_health=0.85,
            btc_health=0.85,
            score=0.8,
            confidence=85.0,
            approved=True,
            status="FILLED",
            created_at=now - timedelta(days=10 - i)
        )
        db_session.add(sig)
        sigs.append(sig)
    db_session.commit()
    return sigs


class TestStrategyLabBackend:

    def test_get_templates(self):
        response = client.get("/strategy-lab/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["name"] == "Trend Following (EMA + Whale flow)"

    def test_save_and_get_strategies(self, db_session):
        # Clean existing
        db_session.query(SavedStrategy).delete()
        db_session.commit()

        # Save new
        strategy_data = {
            "name": "Test Strategy",
            "description": "A unit testing description",
            "rules": [
                {"type": "indicator", "param": "trend_score", "operator": ">=", "value": 0.5}
            ],
            "parameters": {
                "stop_loss_pct": 1.5,
                "take_profit_pct": 4.5,
                "risk_pct": 1.0
            }
        }
        response = client.post("/strategy-lab/save", json=strategy_data)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        saved_id = response.json()["id"]

        # Get saved
        response = client.get("/strategy-lab/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        matching = [s for s in data if s["id"] == saved_id]
        assert len(matching) == 1
        assert matching[0]["name"] == "Test Strategy"

        # Update strategy
        updated_data = {
            "id": saved_id,
            "name": "Updated Strategy",
            "description": "Updated desc",
            "rules": [
                {"type": "indicator", "param": "trend_score", "operator": ">=", "value": 0.6}
            ],
            "parameters": {
                "stop_loss_pct": 2.0,
                "take_profit_pct": 6.0,
                "risk_pct": 2.0
            }
        }
        response = client.post("/strategy-lab/save", json=updated_data)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Get updated
        response = client.get("/strategy-lab/saved")
        assert response.status_code == 200
        data = response.json()
        matching_updated = [s for s in data if s["id"] == saved_id]
        assert len(matching_updated) == 1
        assert matching_updated[0]["name"] == "Updated Strategy"

        # Delete
        response = client.delete(f"/strategy-lab/delete/{saved_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Verify deleted
        response = client.get("/strategy-lab/saved")
        assert saved_id not in [s["id"] for s in response.json()]

    def test_backtest_endpoint(self, seed_signals):
        req_data = {
            "name": "Custom Test Backtest",
            "description": "Testing simulated backtests",
            "rules": [
                {"type": "indicator", "param": "trend_score", "operator": ">=", "value": 0.5}
            ],
            "parameters": {
                "stop_loss_pct": 2.0,
                "take_profit_pct": 5.0,
                "risk_pct": 1.5
            }
        }
        response = client.post("/strategy-lab/backtest", json=req_data)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "performance" in data
        assert "trades" in data
        assert "equity_curve" in data
        assert data["summary"]["total_signals_scanned"] >= 10

    def test_optimize_endpoint(self, seed_signals):
        req_data = {
            "rules": [
                {"type": "indicator", "param": "trend_score", "operator": ">=", "value": 0.5}
            ],
            "param_ranges": {
                "stop_loss_pct": [1.5, 2.0],
                "take_profit_pct": [4.0, 5.0],
                "risk_pct": [1.0]
            }
        }
        response = client.post("/strategy-lab/optimize", json=req_data)
        assert response.status_code == 200
        data = response.json()
        assert "best_parameters" in data
        assert "trials" in data
        assert len(data["trials"]) > 0

    def test_walk_forward_endpoint(self, seed_signals):
        req_data = {
            "rules": [
                {"type": "indicator", "param": "trend_score", "operator": ">=", "value": 0.5}
            ],
            "window_size_days": 3,
            "test_size_days": 1,
            "step_days": 1,
            "max_windows": 5
        }
        response = client.post("/strategy-lab/walk-forward", json=req_data)
        assert response.status_code == 200
        data = response.json()
        assert "windows" in data
        assert "avg_train_sharpe" in data
        assert "avg_test_sharpe" in data

    def test_monte_carlo_endpoint(self, seed_signals):
        req_data = {
            "rules": [
                {"type": "indicator", "param": "trend_score", "operator": ">=", "value": 0.5}
            ],
            "initial_capital": 10000.0,
            "num_simulations": 100,
            "num_trades": 20
        }
        response = client.post("/strategy-lab/monte-carlo", json=req_data)
        assert response.status_code == 200
        data = response.json()
        assert "simulations" in data
        assert "metrics" in data
        assert "probability_of_ruin_pct" in data["metrics"]
        assert "avg_drawdown_pct" in data["metrics"]

    def test_sensitivity_endpoint(self, seed_signals):
        req_data = {
            "rules": [
                {"type": "indicator", "param": "trend_score", "operator": ">=", "value": 0.5}
            ],
            "parameter_to_perturb": "stop_loss_pct",
            "base_value": 2.0
        }
        response = client.post("/strategy-lab/sensitivity", json=req_data)
        assert response.status_code == 200
        data = response.json()
        assert "parameter" in data
        assert "base_value" in data
        assert "sensitivity_matrix" in data
        assert len(data["sensitivity_matrix"]) == 5

    def test_ai_generate_and_analyze_endpoints(self):
        # AI generate
        req_generate = {
            "style": "Trend Following",
            "risk_level": "Medium"
        }
        response = client.post("/strategy-lab/ai-generate", json=req_generate)
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "parameters" in data
        assert "name" in data

        # AI analyze
        req_analyze = {
            "rules": data["rules"],
            "metrics": {
                "total_pnl": 1500.0,
                "win_rate_pct": 65.0,
                "sharpe_ratio": 1.8,
                "max_drawdown_pct": 8.5
            }
        }
        response = client.post("/strategy-lab/ai-analyze", json=req_analyze)
        assert response.status_code == 200
        analysis_data = response.json()
        assert "strengths" in analysis_data
        assert "weaknesses" in analysis_data
        assert "improvements" in analysis_data
        assert "missing_filters" in analysis_data
