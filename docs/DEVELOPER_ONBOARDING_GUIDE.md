# DEVELOPER ONBOARDING & ARCHITECTURE GUIDE — SPRINT 23

Welcome to the **NEXUS Decision Intelligence Platform** development team.
This guide will get you onboarded and running within **one hour**.

---

## 1. Quick Onboarding Walkthrough

### Python Environment (>= 3.13)
The platform is built on modern Python 3.13 features.
```bash
# Configure local Python version using pyenv
pyenv install 3.13.1
pyenv global 3.13.1

# Configure poetry to target the local Python installation
poetry env use 3.13.1
```

### Dependency Installation
```bash
poetry install --no-root
# Or install requirements manually via pip
pip install -r requirements.txt
```

### Local Database Seeding (SQLite)
A local, fully reproducible SQLite validation environment is pre-configured.
```bash
# Set environment to development fallback targets
export API_ENV=development
export DATABASE_URL=sqlite:///decision_engine.db

# Initialize database schemas and tables
python database.py

# Seed users, signals, notifications, and watchlists
python seed_data.py
```

---

## 2. Cognitive Architecture & Subsystems

NEXUS utilizes a Clean Architecture with a strict decoupling between routing, coordination, and business services.

### Global Intelligence Orchestrator (`core/orchestrator/`)
The platform’s central coordination hub executes an 11-stage sequential reasoning pipeline:
1. **Market Context**: Aggregates OHLCV and live indicator series.
2. **Market Regime**: Analyzes narrative clusters, structural trends, and sector rotations.
3. **Decision Memory**: Conducts cosine similarity checks against historical ledger memories.
4. **Pattern Discovery**: Highlights winning patterns via deterministic K-Means clustering.
5. **Risk Engine**: Scores symbols against maximum exposure bounds.
6. **AI Debate**: Runs structured, multi-agent AI panel evaluations.
7. **Counterfactual Engine**: Analyzes alternate scenario executions.
8. **Confidence Calibration**: Calculates Expected Calibration Error (ECE) and Brier Score.
9. **Priority Ranking**: Computes composite multi-dimensional opportunity scores.
10. **Explainability**: Answers mandatory Why/Why now/Why not criteria.
11. **Executive Recommendation**: Publishes final strategic recommendations.

---

## 3. REST API Endpoint Specifications

All intelligence and orchestration routes are mounted under `api/routes/intelligence.py` with the following parameters:

### Orchestrate Pipeline (`POST /intelligence/orchestrate`)
- **Query Params**: `symbol: str = "BTC"`
- **Response Shape**: Returns complete 11-stage pipeline result dictionaries and context traces.

### Strategic Briefing (`GET /intelligence/brief`)
- **Query Params**: `symbol: str = "BTC"`
- **Response Shape**: Includes Highest Confidence Opportunity, Composite Score, and Invalidation triggers.

### System Timeline (`GET /intelligence/timeline`)
- **Query Params**: `limit: int = 50`
- **Response Shape**: Chronological list of EventBus timeline events.

---

## 4. Testing & Verification Matrix

Run the entire suite of **1,335 tests** to ensure 100% regression safety:
```bash
# Run pytest globally
poetry run pytest

# Run specific edge cases tests
poetry run pytest tests/test_edge_cases.py

# Run sequential orchestrator tests
poetry run pytest tests/test_intelligence_orchestration.py
```
