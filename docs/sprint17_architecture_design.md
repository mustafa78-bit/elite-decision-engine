# SPRINT 17 — NEXUS DECISION OPERATING SYSTEM (DOS) SPECIFICATION
## MASTER ARCHITECTURE & DESIGN SPECIFICATION (PHASE A)

This document establishes the official architectural candidate design, data ownership contracts, system flow models, performance budgets, test plans, and security reviews for Sprint 17.

---

## SECTION 1: MASTER SYSTEM OVERVIEW

```
                               ┌──────────────────────────────────────────────┐
                               │            Founder Decision Input            │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
┌───────────────────────┐              ┌──────────────────────────────┐              ┌─────────────────────────┐
│  Market Memory        │─────────────>│    Unified Decision Kernel   │<─────────────│   AI Debate Engine      │
│  (Regime Trackers)    │              │    (12-Stage Pipeline)       │              │   (Multi-Agent Debate)  │
└───────────────────────┘              └──────────────┬───────────────┘              └─────────────────────────┘
                                                      │
                                                      ▼
┌───────────────────────┐              ┌──────────────────────────────┐              ┌─────────────────────────┐
│  Decision Simulator   │<─────────────│    NEXUS Decision Ledger     │─────────────>│   Counterfactual        │
│  (Pre-Flight Risk)    │              │    (Immutable Logs & Events) │              │   Engine (Post-Hoc)     │
└───────────────────────┘              └──────────────┬───────────────┘              └─────────────────────────┘
                                                      │
                                                      ▼
┌───────────────────────┐              ┌──────────────────────────────┐              ┌─────────────────────────┐
│  Cognitive Bias       │─────────────>│      Decision DNA Engine     │<─────────────│   Adaptive Coaching     │
│  Detection Engine     │              │      (Founder Profile)       │              │   Engine (Insights)     │
└───────────────────────┘              └──────────────┬───────────────┘              └─────────────────────────┘
                                                      │
                                                      ▼
                                       ┌──────────────────────────────┐
                                       │     Trust Engine 2.0         │
                                       │     & Decision Quality Score │
                                       └──────────────────────────────┘
```

---

## SECTION 2: THE 15 SPRINT EPICS

### EPIC 1 — Decision DNA Engine

#### 1. System Intent & Architecture
The **Decision DNA Engine** tracks the Founder’s fundamental behavioral traits, biases, strategies, and performance over time to build a persistent, adaptive decision-making profile (DNA profile). It maps quantitative metrics directly to qualitative cognitive fingerprints.

#### 2. Domain Model & DB Schema Definition
```python
# database.py Concept Model Definition
class DecisionDNA(Base):
    __tablename__ = "decision_dna"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Behavioral Metrics
    risk_profile = Column(String(50), default="MODERATE") # CONSERVATIVE, MODERATE, AGGRESSIVE
    decision_speed_seconds = Column(Float, default=0.0)
    average_holding_duration_seconds = Column(Float, default=0.0)

    # Market Conditions Preferences
    preferred_market_regimes = Column(JSON, default=list) # e.g. ["BULL", "EUPHORIA"]
    preferred_strategies = Column(JSON, default=list) # e.g. ["EMA_CROSS", "BREAKOUT"]

    # Win/Loss & Confidence History
    win_loss_ratio = Column(Float, default=0.0)
    confidence_calibration_score = Column(Float, default=0.0) # Brier score deviation
    trading_discipline_score = Column(Float, default=100.0) # Penalty-based discipline

    # Behavioral Tendency Fingerprint
    behavioral_tendencies = Column(JSON, default=dict) # e.g. {"loss_aversion_ratio": 1.2}

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 3. Data Ownership
* **Owner**: `DecisionDNAService` (under `services/dna/`)
* **Inputs**: Historical signals, executed paper trades, emotion-grounded journal entries.
* **Outputs**: Updated profiles published to `/ollo/os/dna` and downstream to the simulator and debate moderator.

#### 4. API Contract
```json
{
  "method": "GET",
  "path": "/api/v1/dna",
  "response": {
    "user_id": 1,
    "risk_profile": "AGGR_GROWTH",
    "decision_speed_seconds": 12.4,
    "average_holding_duration_seconds": 86400,
    "preferred_market_regimes": ["BULL_EUPHORIA", "VOLATILITY_EXPANSION"],
    "preferred_strategies": ["EMA_PULLBACK"],
    "win_loss_ratio": 1.85,
    "confidence_calibration_score": 0.88,
    "trading_discipline_score": 92.5,
    "behavioral_tendencies": {
      "fomo_vulnerability": 0.15,
      "loss_aversion_factor": 1.45,
      "revenge_trading_propensity": 0.05
    }
  }
}
```

---

### EPIC 2 — Cognitive Bias Detection Engine

#### 1. System Intent & Architecture
Detect and quantify classic behavioral pitfalls using deterministic evaluation patterns mapped directly from trades, journal entries, and decisions.

#### 2. Bias Detection Framework
* **FOMO (Fear Of Missing Out)**: Triggered when user enters a trade *after* the price has already pumped >3% from signal entry within <5 minutes, with confidence >90%.
* **Revenge Trading**: Triggered when a trade is opened within 15 minutes of a severe loss (SL hit), at twice the position size or with a lower score.
* **Confirmation Bias**: User ignores >3 bearish alerts / risk warnings from the AI Council and manually overrides to open a LONG position anyway.
* **Loss Aversion**: User keeps a losing trade open >2 hours after the stop-loss price was breached or manually moves stop loss further down.
* **Anchoring**: User refuses to adjust take-profit target despite strong volume trend reversal because of a specific round number.
* **Recency Bias**: User increases exposure after 3 consecutive wins, disregarding risk rules.
* **Overconfidence**: Decision confidence is set to 100% on a trade with scoring < 60%.
* **Gambler's Fallacy**: Assuming a correction must occur purely because price trended in one direction for 5 consecutive periods.

#### 3. Domain Model & DB Schema Definition
```python
class CognitiveBiasLog(Base):
    __tablename__ = "cognitive_bias_logs"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, nullable=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    bias_type = Column(String(50), nullable=False) # e.g. FOMO, REVENGE_TRADING
    confidence = Column(Float, default=0.0) # confidence of the detector (0 to 1)
    evidence = Column(JSON, default=dict) # Details supporting the detection
    explanation = Column(Text, nullable=False)
    suggested_improvement = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 4. API Contract
```json
{
  "method": "GET",
  "path": "/api/v1/biases",
  "response": {
    "detected_biases": [
      {
        "bias_type": "FOMO",
        "confidence": 0.94,
        "evidence": {
          "signal_entry_price": 50000.0,
          "actual_entry_price": 52100.0,
          "time_difference_seconds": 180
        },
        "explanation": "You bought BTCUSDT 4.2% higher than the entry trigger within 3 minutes of signal release.",
        "suggested_improvement": "Wait for a pull-back to 50500.0 or utilize automated limit orders."
      }
    ]
  }
}
```

---

### EPIC 3 — Decision Simulator

#### 1. System Intent & Architecture
A pre-flight sandbox where the Founder simulates alternative entry and exit bounds under specific risk/reward parameters prior to locking in live execution.

#### 2. Domain Model & Class Contract
```python
class DecisionSimulationRequest(BaseModel):
    symbol: str
    side: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float

class DecisionSimulationResponse(BaseModel):
    expected_risk_usd: float
    historical_similarity_score: float
    best_case_return_usd: float
    worst_case_loss_usd: float
    expected_drawdown_percent: float
    alternative_entries: list[float]
    alternative_exits: list[float]
    risk_reward_comparison_ratio: float
```

#### 3. Data Flow and Sequence
1. User provides parameters via UI / OLLO.
2. `DecisionSimulator` pulls past market memory matching current indicators.
3. Calculates drawdown distribution and displays best/worst historical outcomes.

---

### EPIC 4 — AI Debate Engine

#### 1. System Intent & Architecture
Runs a structured multi-agent debate among specialized synthetic cognitive agents. Each agent maintains a distinct trading mandate. A moderator aggregates the outcome.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Bull Analyst   │     │  Bear Analyst   │     │  Risk Officer   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────┬───────┴───────────────────────┘
                         ▼
             ┌──────────────────────┐     ┌─────────────────────┐
             │ Portfolio Manager    │─────>│ Moderator (Consensus│
             │ & Macro Analyst      │     │  & Final Verdict)   │
             └──────────────────────┘     └─────────────────────┘
```

#### 2. Multi-Agent Role Matrix
* **Bull Analyst**: Maximizes bullish sentiment, focusing on technical indicators, EMA trend support, and breakout configurations.
* **Bear Analyst**: Maximizes bearish thesis, focusing on resistance blocks, supply zones, RSI overbought levels, and volume divergence.
* **Risk Officer**: Enforces strict exposure limits, leverage buffers, and maximum drawdowns.
* **Portfolio Manager**: Evaluates multi-asset correlation, cash balances, and overall sector exposure.
* **Macro Analyst**: Integrates overnight news trends, rates, funding rates, and macroeconomic indices.
* **Moderator**: Orchestrates debate turns, calculates consensus vs. disagreement metrics, and issues the final grounded recommendation.

#### 3. API Contract
```json
{
  "method": "POST",
  "path": "/api/v1/debate",
  "response": {
    "debate_id": "deb_77263",
    "consensus_score": 0.72,
    "disagreement_points": [
      "Bull Analyst emphasizes EMA support; Bear Analyst identifies severe 4h volume exhaustion."
    ],
    "minority_opinion": "Risk Officer recommends decreasing position size by 50% due to highly volatile BTC funding rates.",
    "final_recommendation": "APPROVE_HALF_SIZE",
    "transcript": [
      {"role": "Bull Analyst", "statement": "Technical structures support immediate upside continuation..."},
      {"role": "Bear Analyst", "statement": "Divergence indicators signal immediate reversal risk..."}
    ]
  }
}
```

---

### EPIC 5 — Counterfactual Engine

#### 1. System Intent & Architecture
Evaluates post-hoc decisions by comparing what *actually* happened in a trade against what *would* have happened under alternative strategies.

#### 2. Counterfactual Simulation Array
* **Different Stop Loss**: What if stop loss was placed at 1x ATR instead of 2x ATR?
* **Different Take Profit**: What if take profit had been split 50/50 instead of 100% exit at TP1?
* **Delayed Entry**: What if entry was delayed by 15 minutes to allow pullback confirmation?
* **Earlier Exit**: What if exit happened immediately on the first bearish 15m candle close?
* **Half Position Size**: How would equity curve drift if only 50% risk exposure was run?
* **No Trade Scenario**: What is the net portfolio delta if this trade had been entirely skipped?

#### 3. DB Schema Definition
```python
class CounterfactualAnalysis(Base):
    __tablename__ = "counterfactual_analyses"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, nullable=False, index=True)

    actual_pnl = Column(Float, nullable=False)
    no_trade_delta = Column(Float, default=0.0)

    half_size_pnl = Column(Float)
    tight_stop_pnl = Column(Float)
    split_tp_pnl = Column(Float)
    delayed_entry_pnl = Column(Float)

    optimal_scenario = Column(String(100))
    optimal_potential_pnl = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

### EPIC 6 — Adaptive Founder Coaching

#### 1. System Intent & Architecture
Acts as the algorithmic executive coach. Rather than giving generic feedback, it continuously parses the `DecisionDNA` and `CognitiveBiasLog` to generate evidence-backed, prescriptive lessons.

#### 2. Schema Blueprint
```python
class CoachingRecommendation(Base):
    __tablename__ = "coaching_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    category = Column(String(50)) # e.g. PATTERN_BREAK, HABIT_STRENGTHENING
    feedback = Column(Text, nullable=False)

    # Evidence Mapping
    related_bias_ids = Column(JSON, default=list)
    related_trade_ids = Column(JSON, default=list)

    suggested_action = Column(String(255))
    dismissed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

### EPIC 7 — Market Memory Engine

#### 1. System Intent & Architecture
Maintains historical market regimes. It links every single signal and trade directly to the macro market regime at the moment the decision was created.

#### 2. Regime Identifiers
* **BULL**: Steady upward trend (EMA20 > EMA50 > EMA200).
* **BEAR**: Steady downward trend (EMA20 < EMA50 < EMA200).
* **SIDEWAYS**: Price consolidates inside tight Bollinger Bands.
* **PANIC**: Extreme volatility spike downward (RSI < 20, ATR increases >100% in 1h).
* **RECOVERY**: Aggressive rebound from severe low with heavy volume accumulation.
* **EUPHORIA**: Exponential price extension above historical outer bands (RSI > 85).

```python
class MarketRegimeSnap(Base):
    __tablename__ = "market_regime_snaps"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    symbol = Column(String(20), nullable=False)

    regime_type = Column(String(30), nullable=False) # e.g. PANIC, EUPHORIA
    volatility_metric = Column(Float)
    rsi_14 = Column(Float)
    funding_rate = Column(Float)
```

---

### EPIC 8 — Unified Decision Timeline

#### 1. System Intent & Architecture
A single chronologically indexable event timeline. It links the lifecycle of a decision from market indicators all the way to ultimate machine learning lessons.

#### 2. Timeline Sequence Flow
```
Market State (Memory)
       │
       ▼
Signal Emitted (Discovery Engine)
       │
       ▼
AI Council Analysis & Debate (Debate Engine)
       │
       ▼
Founder Decision (Observe -> Trust -> Decide)
       │
       ▼
Paper Order Dispatched (Execution Loop)
       │
       ▼
Journal Entry Formulated (Emotional Context)
       │
       ▼
Outcome Computed (Trade Closes)
       │
       ▼
Counterfactual Evaluation (Alternative Scenarios)
       │
       ▼
Decision DNA Upgraded & Profile Calibrated
```

#### 3. API Contract
```json
{
  "method": "GET",
  "path": "/api/v1/timeline",
  "query": {"filter": "replays", "limit": 10},
  "response": {
    "timeline_events": [
      {
        "timestamp": "2026-07-29T10:00:00Z",
        "stage": "MARKET_CONTEXT",
        "details": {"regime": "RECOVERY", "volatility": "HIGH"}
      },
      {
        "timestamp": "2026-07-29T10:01:00Z",
        "stage": "SIGNAL",
        "details": {"id": 482, "symbol": "ETHUSDT", "side": "LONG"}
      },
      {
        "timestamp": "2026-07-29T10:01:30Z",
        "stage": "AI_DEBATE",
        "details": {"debate_id": "deb_77263", "verdict": "APPROVE"}
      }
    ]
  }
}
```

---

### EPIC 9 — Trust Engine 2.0

#### 1. System Intent & Architecture
Continuously calculates trust metrics between human intuition and AI council outputs, assessing calibration curves over long horizons.

#### 2. Key Metrics
* **AI Council Accuracy**: Successful calls / total calls.
* **Founder Accuracy**: Successful manual overrides / total overrides.
* **Agreement Rate**: Pct of times human follows AI Council recommendation.
* **Disagreement Rate**: Pct of times human overrides AI Council recommendation.
* **Confidence Calibration Deviation (Brier Score)**: Deviation of confidence percentage from empirical win rate.

---

### EPIC 10 — Decision Quality Score

#### 1. System Intent & Architecture
Aggregates performance and behavioral vectors into a single authoritative **Decision Quality Score (DQS)** ranging from 0 to 100.

#### 2. Formulation Weights
```
DQS = (Evidence Quality * 0.15)
    + (Timing Accuracy  * 0.15)
    + (Risk Compliance  * 0.20)
    + (Execution Precision * 0.10)
    + (Psychological Calibration * 0.15)
    + (Discipline Index * 0.15)
    + (Outcome Score * 0.10)
```

---

### EPIC 11 — Founder Dashboard 2.0

#### 1. Workspace Configuration
Integrates advanced metrics panels into the Command Deck dark HUD configuration.

* **Decision Health**: Displays historical rolling DQS trends.
* **Mental Performance**: Monitors physical/emotional stress mapped from journals.
* **Bias Heatmap**: Highlights active biases (e.g. FOMO vs Loss Aversion).
* **Confidence Calibration**: Scatter-plots confidence against actual win percentage.
* **Decision Calendar**: Chronological layout marking wins/losses/biases over the month.

---

### EPIC 12 — Strategic Intelligence

#### 1. System Intent & Architecture
Directs proactive strategic alerts to the command deck, letting the Founder know exactly what setup matches their "optimal trading sweet-spot".

#### 2. Alert Types
* **Sweet-Spot Alert**: "Market is in SIDEWAYS regime, which historically has an 82% win rate for your EMA_PULLBACK strategy."
* **System Warning**: "You are currently showing signs of Recency Bias. We highly recommend decreasing leverage to 1x for the next 24 hours."

---

### EPIC 13 — Autonomous Insight Generator

#### 1. System Intent & Architecture
An autonomous agent that compiles a daily intelligence report summarizing multi-engine telemetry.

#### 2. Report Sections
1. **Yesterday’s Summary**: Total positions filled, aggregate PnL, overall DQS.
2. **Weekly Progress**: Metrics relative to prior 7 days.
3. **Open Risks**: Multi-asset exposure alert levels.
4. **Sweet-Spot Opportunities**: Strategy/regime alignment.
5. **Lessons Learned**: Active bias trends.
6. **AI Council Recommendations**: Actionable items for the morning brief.

---

### EPIC 14 — Decision Intelligence APIs

All backend routers must export compliant, documented JSON responses. No speculative mock structures. Fully mapped through custom DTO models.

#### 1. Endpoints List
* `GET /api/v1/dna` -> Epic 1 DNA Profile
* `GET /api/v1/coaching` -> Epic 6 Recommendations
* `GET /api/v1/biases` -> Epic 2 Active Biases
* `POST /api/v1/simulator` -> Epic 3 Simulator Sandboxes
* `POST /api/v1/debate` -> Epic 4 Debate Orchestration
* `GET /api/v1/timeline` -> Epic 8 Interactive Timeline
* `GET /api/v1/counterfactuals` -> Epic 5 Scenarios

---

### EPIC 15 — Architecture Hardening

#### 1. Performance Budgets
* **Debate Engine Orchestration**: Max execution time < 800ms.
* **Database Ledger Write**: Max transaction lock time < 50ms.
* **Simulator Backtest**: Execution latency < 350ms.

#### 2. Security & Compliance Review
* **Strict JWT Authentication**: Every protected REST API must validate token signatures.
* **Rate Limits**: Limit timeline search endpoints to 20 calls/minute.

#### 3. Observability & Telemetry Plan
* Track latency patterns via standard prometheus instrumentation.
* Capture bias detection triggers under the engineering telemetry index.

---

## SECTION 3: SYSTEM SEQUENCING & DATA INTEGRATION

The following sequence diagram details the runtime operations from a new discovery event to final DNA calibration:

```
Founder UI             OLLO OS Service        AI Debate Engine       Simulator Engine        DecisionDNA
   │                         │                       │                      │                     │
   │─── Query brief ────────>│                       │                      │                     │
   │                         │─── Query Context ────>│                      │                     │
   │                         │                       │─── Run Debate ──────>│                     │
   │                         │                       │<── Debate Transcript │                     │
   │                         │                                              │                     │
   │                         │─── Pre-flight simulation ───────────────────>│                     │
   │                         │<────────────────── Return Scenarios ─────────│                     │
   │                         │                                                                    │
   │<── Render Options ──────│                                                                    │
   │                                                                                              │
   │─── Manual Decision ─────────────────────────────────────────────────────────────────────────>│
   │                                                                                              │── Calibrate
```

---

## SECTION 4: TEST STRATEGY & ASSURANCE

All new modules must be verified utilizing deterministic test suites under SQLite in-memory modes.

### Test Matrix
1. `tests/test_dna_engine.py`: Verifies profiling, Speed processing, holding durations, and calibration updates.
2. `tests/test_cognitive_biases.py`: Feeds anomalous trade logs to verify the confidence and correctness of FOMO, Revenge Trading, and Overconfidence detectors.
3. `tests/test_debate_agents.py`: Simulates debate turn-taking and verifies final consensus logic.
4. `tests/test_counterfactual_engine.py`: Feeds mock closed trades and verifies calculated mathematical deltas.
