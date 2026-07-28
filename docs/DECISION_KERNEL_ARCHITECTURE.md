# ARCHITECTURE REPORT: Unified Decision Kernel (NEXUS Cognitive Core)

> **Status**: Frozen / Approved | **Target Version**: v2.0.0 | **Author**: Jules

---

## 1. Decision Lifecycle

Every decision in the NEXUS Cognitive Core undergoes a strict, sequential, single-path progression. No alternative routes, partial executions, or short-circuits bypassing these cognitive stages are permitted:

```
      DecisionRequest
            │
            ▼
     DecisionContext (Observe & Understand)
            │
            ▼
     Relationship Graph 2.0 (Connect)
            │
            ▼
     DecisionEvidence Collection (Evaluate)
            │
            ▼
     DecisionReasoning Chain (Reason)
            │
            ▼
     Trust & Calibration (Calibrate)
            │
            ▼
     Risk & Portfolio (Safeguard)
            │
            ▼
     DecisionResult Generation (Decide)
            │
            ▼
     DecisionTimeline Recording (Remember)
```

### Cognitive Flow Stages

1. **Observe & Understand**:
   The Decision Kernel receives a `DecisionRequest` and pairs it with the complete system-wide `DecisionContext` containing raw market ticks, indicators, order history, and portfolio status.
2. **Connect**:
   The `KnowledgeGraph` is queried to extract immediate and multi-hop relationships (e.g., related whales, coin correlation, strategy overlaps, narrative clustering).
3. **Evaluate**:
   Empirical facts are structured as `DecisionEvidence` items. Each piece of evidence is rated for sources, confidence, and trust weights.
4. **Reason**:
   A deterministic multi-factor scoring algorithm evaluates the evidence items sequentially. Reasoning steps are appended as `DecisionReasoning` records.
5. **Calibrate**:
   Historical error calibration, Expected Calibration Error (ECE), and Trust factors are applied, scaling LLM confidence and technical ratings to eliminate biases.
6. **Safeguard**:
   The candidate is passed to the Risk Engine and Portfolio engine to evaluate absolute limits, drawdown levels, and execute position-sizing.
7. **Decide**:
   The Kernel aggregates all findings and generates a frozen, immutable `DecisionResult` indicating the exact recommendation.
8. **Remember**:
   The complete decision and contextual trace is committed to the chronological `DecisionTimeline` and saved into the persistent `Founder Memory`.

---

## 2. DecisionResult Contract

`DecisionResult` serves as the **single source of truth** for decisions across the entire platform. Every consumer—including the API routers, WebSockets, Frontend Dashboard, OLLO Assistant, Replay Engine, and Simulator—must consume and rely solely on this schema.

### Stable Schema Definition (dataclass)

```python
@dataclass
class DecisionResult:
    # 1. Core Identification
    decision_id: str                   # Cryptographically unique string UUID or SHA-256
    symbol: str                        # Target ticker (e.g., BTCUSDT)
    side: str                          # Direction (LONG, SHORT, WATCH)
    decision: str                      # Final action recommendation (STRONG_APPROVE, APPROVE, WATCH, REJECT)
    timestamp: str                     # ISO-8601 UTC timestamp

    # 2. Score Metrics
    score: float                       # Raw input technical score (0.0 - 1.0)
    confidence: float                  # Calibrated confidence score (0.0 - 100.0)
    probability: float                 # Estimated win probability (0.0 - 1.0)
    risk_score: float                  # Risk priority multiplier (0.0 - 1.0)
    priority: float                    #Composite executive priority score (0.0 - 100.0)

    # 3. Contextual Subsystems
    trust: dict[str, Any]              # Trust scores, calibration errors (ECE, Brier, regret)
    risk: dict[str, Any]               # Risk engine checks (BTC health, exposure, limits, reasons)
    portfolio_impact: dict[str, Any]   # ATR-based position size, USD value, current exposure, margin
    market_regime: dict[str, Any]      # Regime categorization, trend strength, volatility class
    learning_context: dict[str, Any]   # Past trade patterns matched, active lessons, similar outcomes
    calibration_status: dict[str, Any] # Confidence calibration scales and Brier metrics
    graph_context: dict[str, Any]      # Influential graph nodes, connection degree, subgraphs
    advisor_votes: dict[str, Any]      # AI Council voting details, agent-by-agent scores

    # 4. Human-Readable Explanations
    reasons: list[str]                 # Primary bulleted reasons for the decision
    warnings: list[str]                # Highlighted hazards, conflicts, or caveats
    signals: list[str]                 # Technical/structural signals triggered
    founder_summary: str               # Plain-English Executive briefing sentence

    # 5. Full Cognitive Traces
    evidence: list[DecisionEvidence]   # Frozen collection of empirical evidence pieces
    reasoning: list[DecisionReasoning] # Immutable step-by-step reasoning steps
    timeline: list[TimelineEvent]      # Sequential record of the processing steps
    metadata: dict[str, Any]           # Replay parameters, versioning, system load, model metrics
```

### Backward Compatibility Mapping
To prevent any disruption to legacy components or conftest fixtures:
- Property getters are exposed to seamlessly resolve `result.score`, `result.confidence`, and `result.risk_score`.
- Any legacy system can treat `DecisionResult` as a drop-in replacement for `decision.models.DecisionResult`.

---

## 3. DecisionKernel Responsibilities

A strict architectural separation of concerns is maintained to keep the Decision Kernel highly stable and prevent scope creep:

### What the Kernel OWNS
1. **Cognitive Orchestration**: Walking requests through the 12-stage cognitive pipeline sequentially.
2. **System Interface**: Unifying incoming metrics, portfolio states, and graph nodes.
3. **Decision Assembly**: Instantiating and locking the final immutable `DecisionResult`.
4. **Timeline Creation**: Maintaining complete provenance of how a decision was arrived at.
5. **Evidence Aggregation**: Validating evidence sources and assigning appropriate trust weights.

### What the Kernel DOES NOT Own
1. **Indicator Calculation**: Entrusted fully to `market_data/indicators.py` or technical scoring engines.
2. **Market Data Collection**: Performed by `market_data/collector.py` or the `MarketDataService`.
3. **Database Persistence**: Handled by the database sessions (`database.py`) and DAO layer.
4. **Portfolio Execution**: Handled by the `TradeEngine`, `OrderManager`, and paper execution loops.
5. **Notification Delivery**: Dispatched by `NotificationDispatcher` via WebSockets and external alerts.

---

## 4. Extension Points

The Decision Kernel must remain completely generic. It does not contain hardcoded logic for how trust, learning, or discovery is calculated. Instead, it interacts via **abstract protocol boundaries**:

```
 ┌───────────────┐        ┌────────────────┐        ┌──────────────────┐
 │ TrustProtocol │        │ LearningEngine │        │ DiscoveryEngine  │
 └───────┬───────┘        └───────┬────────┘        └────────┬─────────┘
         │                        │                          │
         └────────────────────────┼──────────────────────────┘
                                  ▼
                        ┌──────────────────┐
                        │  DecisionKernel  │
                        └──────────────────┘
```

Future engines can be cleanly registered or injected on initialization:
- **`TrustEngine`**: Returns `trust_score`, `ece_brier_scores`, and mistake registry states.
- **`LearningEngine`**: Returns relevant historical outcomes and advisor-weight adjustments based on reinforcement learning.
- **`DiscoveryEngine`**: Identifies emerging narrative trends, whale-activity clusters, and coin surges.
- **`CalibrationEngine`**: Formulates dynamic probability calibration curves to adjust confidence intervals.

---

## 5. Determinism & Replayability

### The Rule of Determinism
Given identical input states:
$$\text{DecisionRequest} + \text{DecisionContext} \xrightarrow{\text{DecisionKernel}} \text{DecisionResult}$$
The resulting `DecisionResult` must be **mathematically identical and bit-reproducible**.

### Replay Design
1. **Zero External I/O**: The Decision Kernel cannot perform raw HTTP requests, call database sessions, or fetch current time inside its `decide` method. All contextual details must be completely supplied inside the `DecisionContext`.
2. **Cryptographic Integrity**: The `decision_id` is computed as a SHA-256 hash of the request parameters, context values, and replay identifier.
3. **Idempotence**: Re-running the decision with the same inputs produces the same ID, confidence scores, evidence arrays, and priority ranks.
