# SPRINT 20 — NEXUS LEARNING INTELLIGENCE ENGINE SPECIFICATION
## MASTER ARCHITECTURE & DESIGN SPECIFICATION (PHASE A)

This document establishes the official architectural candidate design, data ownership contracts, system flow models, performance budgets, test plans, and security reviews for Sprint 20.

---

## SECTION 1: MASTER SYSTEM OVERVIEW

```
                               ┌──────────────────────────────────────────────┐
                               │       Sprint 17 Reasoning Layer (DOS)        │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
┌───────────────────────┐              ┌──────────────────────────────┐              ┌─────────────────────────┐
│  Decision Memory      │─────────────>│  Pattern Discovery Engine    │<─────────────│  Confidence Calibration │
│  (Integrated Archive) │              │  (Behaviors & Mistakes)      │              │  (Expected Brier Score) │
└───────────────────────┘              └──────────────┬───────────────┘              └─────────────────────────┘
                                                      │
                                                      ▼
┌───────────────────────┐              ┌──────────────────────────────┐              ┌─────────────────────────┐
│  Decision Drift       │<─────────────│   Learning Dashboard         │─────────────>│  Institutional          │
│  (Variance Analysis)  │              │   (API Contracts & Telemetry)│              │  Knowledge Base         │
└───────────────────────┘              └──────────────────────────────┘              └─────────────────────────┘
```

---

## SECTION 2: THE SPRINT 20 EPICS

### Epic 1 — Decision Memory Engine

#### 1. System Intent & Architecture
The **Decision Memory Engine** creates a unified persistent archive for all decision states, DNA parameters, debate outcomes, and counterfactuals, making them fully queryable and indexable.

#### 2. Domain Model & DB Schema Definition
```python
class DecisionMemory(Base):
    __tablename__ = "decision_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    decision_id = Column(Integer, nullable=False, index=True)

    # Snapshot Vectors
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)

    dna_snapshot = Column(JSON, nullable=False) # Stores risk_profile, speed, discipline
    debate_snapshot = Column(JSON) # Debate consensus & final recommendation
    counterfactual_snapshot = Column(JSON) # Alternate scenario calculations
    outcome_snapshot = Column(JSON) # Actual trade outcomes, PnL, exit reasons

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 3. Data Ownership
* **Owner**: `DecisionMemoryService` (under `services/learning/`)
* **Inputs**: Historical databases, DNA profiling service, debate engine, counterfactual analyzer.
* **Outputs**: Searchable event streams mapped directly from trades and decisions.

---

### Epic 2 — Pattern Discovery Engine

#### 1. System Intent & Architecture
Automatically parse the decision memories to detect behavioral patterns, repeated mistakes, and performance sweet-spots over time.

#### 2. Pattern Models
* **Streak Pattern**: Consecutive win/loss loops resulting in overconfidence.
* **Slippage Leak**: Repeated entries with high slippage penalty.
* **Discipline Deterioration**: Successive manual trade overrides.

```python
class DiscoveredPattern(Base):
    __tablename__ = "discovered_patterns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    pattern_name = Column(String(100), nullable=False) # e.g. SLIPPAGE_LEAK
    confidence = Column(Float, default=0.0)
    frequency = Column(Integer, default=1)

    evidence_data = Column(JSON, default=dict)
    relevance_score = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

### Epic 3 — Confidence Calibration

#### 1. System Intent & Architecture
Calculates the alignment between predicted signal confidence and actual trade outcome win rates. It computes the **Expected Calibration Error (ECE)** and Brier score to measure calibration drift.

```python
class CalibrationSnapshot(Base):
    __tablename__ = "calibration_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    brier_score = Column(Float, nullable=False)
    expected_calibration_error = Column(Float, nullable=False)

    confidence_bucket_deltas = Column(JSON, default=dict) # e.g. {"90-100": -0.15}

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

### Epic 4 — Decision Drift Detection

#### 1. System Intent & Architecture
Detects statistical divergence/variance between active trading behavior and historical performance baselines. It alerts when risk metrics or discipline parameters degrade.

```python
class DecisionDriftLog(Base):
    __tablename__ = "decision_drift_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    metric_name = Column(String(50), nullable=False) # e.g. DISCIPLINE_DRIFT, RISK_EXPANSION
    variance_pct = Column(Float, nullable=False)

    severity = Column(String(20), default="INFO") # INFO, WARNING, CRITICAL
    reconciliation_action = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

### Epic 5 — Learning Intelligence Dashboard

#### 1. Workspace Configuration
Exposes learning metrics under the `/api/v1/learning` prefix to build transparent calibration tables and behavioral drift calendars.

#### 2. API Contract
```json
{
  "method": "GET",
  "path": "/api/v1/learning/summary",
  "response": {
    "user_id": 1,
    "calibration": {
      "brier_score": 0.08,
      "ece": 0.12,
      "status": "WELL_CALIBRATED"
    },
    "active_patterns": [
      {
        "pattern_name": "FOMO_REVERSAL",
        "confidence": 0.88,
        "feedback": "You tend to win 12% less on FOMO trades than standard breakout signals."
      }
    ],
    "drift": {
      "discipline_drift_pct": -3.5,
      "severity": "NORMAL"
    }
  }
}
```

---

## SECTION 3: SYSTEM SEQUENCING & FLOWS

```
Decision DOS           Decision Memory         Pattern Discovery      Calibration Engine
     │                         │                       │                       │
     │─── Archive trade ──────>│                       │                       │
     │                         │─── Query memory ─────>│                       │
     │                         │                       │─── Analyze pattern ──>│
     │                         │                       │<── Pattern Results ───│
     │                         │                                               │
     │                         │─── Compute Calibration ──────────────────────>│
     │                         │<────────────────── Return Calibration ────────│
```

---

## SECTION 4: TEST STRATEGY & ASSURANCE

All new services must be tested utilizing deterministic mock-injected SQLite databases.

### Test Matrix
1. `tests/test_decision_memory.py`: Verifies archival consistency and JSON serialization.
2. `tests/test_pattern_discovery.py`: Simulates consecutive trading loops to confirm streak detection confidence.
3. `tests/test_calibration_engine.py`: Computes math formulas for Brier score and Expected Calibration Error.
