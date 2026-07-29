# Sprint 21 — Global Intelligence Orchestrator Architecture

## 1. Overview
The Global Intelligence Orchestrator represents the central cognitive brain of the NEXUS Autonomous Decision Intelligence Platform (ADIP). Rather than operating as a series of independent pipelines or silos, the Orchestrator unifies all 12 platform intelligence subsystems under a single deterministic coordinator, providing a type-safe `UnifiedIntelligenceContext` and a real-time `CrossServiceEventBus`.

## 2. Shared Context Model (`UnifiedIntelligenceContext`)
Every execution cycle aggregates inputs and outputs from downstream intelligence services. The context tracks state across:
- **Decision DNA** (DnaPayload)
- **Bias Engine** (BiasPayload)
- **Decision Simulator** (SimulatorPayload)
- **AI Debate** (DebatePayload)
- **Counterfactual Engine** (CounterfactualPayload)
- **Coaching Engine** (CoachingPayload)
- **Market Memory** (MarketMemoryPayload)
- **Decision Memory** (DecisionMemoryPayload)
- **Pattern Discovery** (PatternPayload)
- **Confidence Calibration** (CalibrationPayload)
- **Drift Detection** (DriftPayload)
- **Risk Engine** (RiskPayload)

## 3. Orchestration Flow & Event Lifecycle
The Orchestrator processes inputs through a pipeline of sequential stages:
1. **Initialize**: Generate a new execution ID and populate the baseline market data inside `UnifiedIntelligenceContext`.
2. **Resolve Priorities**: Use the `PriorityResolver` to determine execution order based on threat matrices or service dependencies.
3. **Dispatch Events**: Emit lifecycle stages onto the `CrossServiceEventBus`.
4. **Execute Pipeline**: Execute each service sequentially or in parallel depending on dependency configurations.
5. **Finalize**: Compute global threat scores, compound confidence metrics, and seal the context.

```
+────────────────────────────────────────────────────────────+
│                 Unified Decision Request                   │
+──────────────────────────────┬─────────────────────────────+
                               │
                               ▼
+────────────────────────────────────────────────────────────+
│            Create UnifiedIntelligenceContext               │
+──────────────────────────────┬─────────────────────────────+
                               │
                               ▼
+────────────────────────────────────────────────────────────+
│          PriorityResolver: Execution Order & Order          │
+──────────────────────────────┬─────────────────────────────+
                               │
                               ▼
+────────────────────────────────────────────────────────────+
│       CrossServiceEventBus: Emit Lifecycle Start Event     │
+──────────────────────────────┬─────────────────────────────+
                               │
                               ▼
+────────────────────────────────────────────────────────────+
│               Execution Pipeline Sequential                │
│  [Market/Decision Memory] -> [DNA/Bias] -> [Sim/Debate]    │
+──────────────────────────────┬─────────────────────────────+
                               │
                               ▼
+────────────────────────────────────────────────────────────+
│     CrossServiceEventBus: Emit Lifecycle Complete Event   │
+────────────────────────────────────────────────────────────+
```

## 4. Service Contracts
Each intelligence service must implement the standard `IntelligenceServiceContract`:
```python
class IntelligenceServiceContract(Protocol):
    def get_service_name(self) -> str: ...
    def get_priority(self) -> int: ...
    def run(self, context: UnifiedIntelligenceContext) -> Any: ...
```

## 5. Failure Recovery Strategy
- **Degraded Fallback**: If a service fails (e.g. timeout or internal exception), the Orchestrator catches the error, logs a telemetry warning, flag the service state as "DEGRADED", and uses pre-configured fallback defaults to allow the pipeline to proceed without complete system crashes.
- **Circuit Breaking**: If any service exceeds 3 consecutive failures, it is temporarily bypassed (returning default fallbacks) for 60 seconds.

## 6. Observability & Performance Budget
- **Performance Budget**: Target maximum processing duration of **50ms** for the orchestration coordination layer. Downstream long-running tasks are mockable or scheduled asynchronously.
- **Telemetry**: Each execution records high-resolution timings (using `time.perf_counter()`) and exports a structured diagnostic payload to the logger.
