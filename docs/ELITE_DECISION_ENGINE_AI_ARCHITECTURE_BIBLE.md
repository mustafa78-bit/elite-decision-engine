# ELITE DECISION ENGINE — AI ARCHITECTURE BIBLE
> **Document Identifier**: EDE-AIB-2026-V1.0
> **Status**: APPROVED TECHNICAL SPECIFICATION
> **Classification**: CONFIDENTIAL / PROPRIETARY
> **Target Audience**: Core AI Engineers, Quant Architects, Integration Engineers

---

## 1. Core Philosophy

The AI Decision Architecture of the Elite Decision Engine is constructed on a single, non-negotiable directive: **"Explainable Decision Intelligence, Guided by Humans, Grounded in Verifiable Evidence."**

Unlike legacy trading platforms that deploy opaque, end-to-end "black-box" deep learning models—where inputs directly yield buy/sell decisions with zero visibility into why—Elite separates **feature observation**, **specialist recommendation**, **evidence aggregation**, **confidence calculation**, **conflict resolution**, and **risk gate validation** into distinct, decoupled pipelines.

```
+-----------------------------------------------------------------------------------+
|                            ELITE OPERATIONAL CORE                                 |
|                                                                                   |
|  [Market Observables] ---> [Specialist Agents] ---> [Evidence Engine]             |
|                                                          |                        |
|                                                          v                        |
|  [Human Verification]  <--- [Risk Validation]  <--- [Consensus/Conflict Engine]   |
+-----------------------------------------------------------------------------------+
```

### Core Tenets
1. **Explainability First**: Every trading recommendation must be accompanied by a human-readable and machine-parsable explanation trace. If a model cannot explain its reasoning, its output is discarded.
2. **AI Recommends, Human Decides**: The AI architecture behaves as an elite advisory council (the "Council") providing highly vetted evidence. The human operator (the "Founder") or the deterministic risk manager holds veto and execution power.
3. **Trace-to-Source Traceability**: Every piece of metadata utilized to score a signal or formulate a decision must point to a specific, immutable source audit trace (e.g., block hash, API fetch timestamp, indicator version).
4. **Zero-Trust Input Sanitization**: All downstream components assume that individual specialist agents can experience failure, bias, or return toxic parameters. Protection is enforced mathematically at the aggregation layer.

---

## 2. System Principles

To guarantee production-grade safety under high-frequency updates, the AI Decision Engine operates under four strict architectural system principles:

| Principle | Description | Implementation Mechanism |
|---|---|---|
| **Mathematical Determinism** | Given the same evidence state, consensus, conflict, and confidence scores must yield identical outputs down to the 8th decimal place. | Pure functional calculations inside the confidence and conflict models, isolated from current system time or network lookups. |
| **Complete Agent Isolation** | Individual specialist agents must never share internal state or directly invoke each other. | Strict share-nothing memory model. Agents communicate solely by returning structured `AgentReport` payloads via a unified registry interface. |
| **Asynchronous Telemetry** | High-frequency telemetry (latency, CPU, memory footprint, request rates) must be streamed side-channel. | Non-blocking telemetry capture via asyncio-decorated execution loops (`_timed_evaluate`) decoupled from the core trade loop. |
| **Error-Resilient Evaluation** | Any agent failure (timeouts, exceptions, schema violations) must result in a graceful fallback degradation. | The `BaseAgent` wrapper catches all execution exceptions, recording an `Evaluation Error` report with a `DIRECTION_PASS` status and `0.0` confidence. |

---

## 3. AI Council Architecture

The Elite Council is a structured consortium of specialized agents. It serves as the primary intelligence collection layer. The architecture utilizes a **Registry Pattern** where each specialized agent is registered with specific metadata parameters: Priority, Weight, and Domain Specialization.

```
                        +------------------------------------+
                        |       Coordinator Service          |
                        +------------------------------------+
                                          |
                      +-------------------+-------------------+
                      |                   |                   |
            +---------v---------+ +-------v---------+ +-------v---------+
            |  Technical Agent  | |   Whale Agent   | |   News Agent    |
            |   (Weight: 1.0)   | |  (Weight: 0.6)  | |  (Weight: 0.8)  |
            +-------------------+ +-----------------+ +-----------------+
                      |                   |                   |
            +---------v---------+ +-------v---------+ +-------v---------+
            |    Macro Agent    | |   Risk Agent    | | Portfolio Agent |
            |   (Weight: 0.5)   | |  (Weight: 1.5)  | |  (Weight: 1.0)  |
            +-------------------+ +-----------------+ +-----------------+
```

### Coordinator Registration & Weight Allocation Matrix

Core config manages the relative importance of council members. Weights represent the relative significance of each specialist's vote during the Consensus stage.

| Specialist Agent | Core Class Name | Default Weight | Priority | Target Subsystem |
|---|---|---|---|---|
| **Technical Agent** | `TechnicalAgent` | `1.0` | `1` (Highest) | Price Action, Momentum, Volume |
| **Whale Agent** | `WhaleAgent` | `0.6` | `3` | Large wallet tracking, orderbook depth |
| **News Agent** | `NewsAgent` | `0.8` | `2` | Natural Language processing, sentiment |
| **Macro Agent** | `MacroAgent` | `0.5` | `4` | Funding rates, open interest, CPI, rates |
| **Risk Agent** | `RiskAgent` | `1.5` | `1` (Veto Power) | Tail risk, regime shifts, drawdowns |
| **Portfolio Agent** | `PortfolioAgent` | `1.0` | `2` | Exposure, correlative limits, sizing |

---

## 4. Agent Framework

Every specialist agent must implement the standard `BaseAgent` interface. Below is the comprehensive architectural blueprint for each of the six core specialists.

### 4.1 Technical Agent
*   **Responsibilities**: Evaluates market trend, momentum, support/resistance, volume spikes, and statistical breakout probabilities.
*   **Input Data**: OHLCV candlestick series (1m, 5m, 15m, 1h, 4h, 1d), orderbook volume imbalances, volatility metrics (ATR, Bollinger Bands).
*   **Output Format**: `AgentReport` representing technical momentum, RSI levels, moving average direction, and volume breakout status.
*   **Confidence Rules**: Confidence scales linearly with trend alignment. If multiple timeframes (15m, 1h, 4h) align in direction, confidence increases by $1.25\times$. If volume breakout is less than $1.5\times$ 20-period average, maximum technical confidence is hard-capped at `50.0`.
*   **Evidence Generation**: Produces data-driven evidence entries indicating specific indicators (e.g., `EMA_CROSS_BULLISH` with fast EMA, slow EMA, and current price).
*   **Failure Handling**: Fallback to historical calculated technical state if active exchange WebSocket is disconnected.
*   **Quality Checks**: Validates that prices are non-zero, candlestick timestamps are contiguous, and volume values are strictly positive.
*   **Extension Strategy**: Easily add momentum oscillators (e.g., MACD, Stochastic RSI) by subclassing the internal indicator extractor without touching the agent output interface.

### 4.2 Whale Agent
*   **Responsibilities**: Monitors on-chain transfers, exchange inflows/outflows, and high-volume orderbook blocks.
*   **Input Data**: Real-time blockchain transactions (ERC20 transfers, native currency transfers > $100k USD equivalent), orderbook wall changes, exchange deposit balances.
*   **Output Format**: `AgentReport` with buy/sell whale pressures and liquidity concentrations.
*   **Confidence Rules**: Confidence increases relative to transaction size and frequency. A single transaction of > $5M USD equivalent on-chain produces `85.0` confidence; multiple micro-whale transactions scale confidence logarithmically:
    $$\text{Confidence} = \min(100.0, 15.0 \times \ln(N_{\text{whale\_tx}} + 1.0))$$
*   **Evidence Generation**: Lists exact transaction hashes, source/destination wallets, and exchange destination flags.
*   **Failure Handling**: Returns `DIRECTION_PASS` and `0.0` confidence if blockchain node latency exceeds 3000ms.
*   **Quality Checks**: Ensures blockchain transaction hash exists, checks for double-counted transactions via a rolling deduplication bloom filter (size: 50,000, error-rate: 0.0001).
*   **Extension Strategy**: Subclass of whale trackers targeting alternative Layer 1/Layer 2 ecosystems (Solana, Arbitrum, Base) and registering them dynamically under the central Whale intelligence interface.

### 4.3 News Agent
*   **Responsibilities**: Parses incoming news feeds, financial press, and developer commits to construct real-time asset sentiment scores.
*   **Input Data**: Reuters, Bloomberg, CoinDesk API feeds, Twitter (X) high-authority posts, Reddit trading forums, GitHub repository activities.
*   **Output Format**: `AgentReport` indicating positive/negative text polarity, news density index, and sentiment impact level.
*   **Confidence Rules**: Confidence is determined by source authority and keyword verification. Standard media feeds default to `50.0` confidence. Direct official developer blog/GitHub releases yield `95.0` confidence.
*   **Evidence Generation**: Emits text snippet quotes, sentiment categorization flags, source author URLs, and publisher classification profiles.
*   **Failure Handling**: Falls back to neutral default state (`DIRECTION_NEUTRAL`, confidence `30.0`) in the event of upstream sentiment API provider downtime.
*   **Quality Checks**: Leverages semantic anomaly detection to identify and flag potential social media manipulation, bot attacks, and flash rumor campaigns.
*   **Extension Strategy**: Integrate direct localized LLMs (e.g., Llama-3-8B-Instruct fine-tuned on financial lexicon) by wrapping the model invocation inside the standard News Agent evaluate call.

### 4.4 Macro Agent
*   **Responsibilities**: Tracks overarching economic variables, interest rates, stablecoin supply indicators, and system funding rates.
*   **Input Data**: Hyperliquid/Binance funding rates, open interest (OI) trends, DXY index, CPI releases, treasury yields, stablecoin printing/burning activities.
*   **Output Format**: `AgentReport` representing macro regime risk (expansionary, contractionary, risk-on, risk-off).
*   **Confidence Rules**: Funding rate anomalies and open interest spikes dictate confidence. If funding rate is near 0.0, Macro confidence is moderate (`50.0`). If funding rate deviates from average by $>3.0$ standard deviations, confidence peaks at `90.0` due to highly elevated market leverage levels.
*   **Evidence Generation**: Includes absolute funding percentage, open interest USD volume change, and stablecoin circulation velocity.
*   **Failure Handling**: Falls back to the latest recorded daily macro parameters cached in the SQLite `test_elite.db` file.
*   **Quality Checks**: Verifies that funding rate bounds do not exceed logical extremes ($\pm 0.5\%$ per 8h) and open interest figures are strictly positive.
*   **Extension Strategy**: Facilitate seamless expansion to traditional macro trackers (like S&P 500, NASDAQ, Gold, or Brent Crude indexes) via external macro provider pipelines.

### 4.5 Risk Agent
*   **Responsibilities**: Monitors tail risk, market regime instability, asset volatility, drawdown levels, and liquidity gaps.
*   **Input Data**: Real-time asset drawdowns, standard deviations, portfolio-wide historical correlation tables, global liquidation values.
*   **Output Format**: `AgentReport` reflecting risk state (e.g., `HIGH_RISK_SHIELD`, `REGIME_STABLE`, `LIQUIDITY_GAP_ALERT`).
*   **Confidence Rules**: Confidence increases with the mathematical extremity of the metric. If volatility exceeds the 30-day 99th percentile, the Risk Agent emits `100.0` confidence recommendation to halt or scale down size.
*   **Evidence Generation**: Pinpoints exact mathematical parameters (e.g., VaR (Value at Risk) 95% threshold exceeded, liquidity slippage estimated > 2.5%).
*   **Failure Handling**: If the risk calculation fails, the Risk Agent defaults to a highly conservative protective state (`DIRECTION_BEARISH`, confidence `100.0`) to trigger emergency system circuit breakers.
*   **Quality Checks**: Ensures portfolio tracking variables represent active, non-closed states.
*   **Extension Strategy**: Enable plugging in advanced quantitative risk architectures (such as Expected Shortfall or GARCH volatility forecasting models) via decoupled statistical calculators.

### 4.6 Portfolio Agent
*   **Responsibilities**: Manages exposure allocation, correlation limits, asset concentration, and tracks realized trading performance.
*   **Input Data**: Current system portfolio allocations, historical asset correlation indices, active trade counts, performance analytics.
*   **Output Format**: `AgentReport` validating if trade fits size targets and matches exposure budgets.
*   **Confidence Rules**: Confidence is determined by direct adherence to portfolio sizing limits. If the portfolio concentration in an asset is $< 5.0\%$, the Portfolio Agent outputs a positive recommendation with `90.0` confidence. If concentration is $> 20.0\%$, it outputs `DIRECTION_PASS` with `100.0` confidence to block further purchases.
*   **Evidence Generation**: Emits active portfolio weights, relative sector allocation, and Sharpe/Sortino ratios of the active strategy.
*   **Failure Handling**: Safe-fail by limiting allocations to micro-sizes ($1.0\%$ max account exposure per trade) if the database query times out.
*   **Quality Checks**: Guarantees that the sum of current asset allocations does not exceed physical equity ($100\%$ limit).
*   **Extension Strategy**: Support multi-account/multi-sub-portfolio isolation layers by exposing an account-index identifier inside the evaluation context.

---

## 5. Agent Communication

The Elite Decision Engine relies on a decoupled, non-blocking asynchronous event communication model. Direct component-to-component invocation is completely forbidden. All specialist outputs, execution ticks, and decisions flow through a centralized high-speed **Event Bus**.

```
                           +------------------------+
                           |  Asynchronous Event Bus|
                           +-----------+------------+
                                       |
                     +-----------------+-----------------+
                     |                                   |
           +---------v---------+               +---------v---------+
           |     Publishers    |               |    Subscribers    |
           |                   |               |                   |
           | Specialist Agents |               | Consensus Engine  |
           | Risk Manager      |               | Dashboard Socket  |
           | System Telemetry  |               | SQLite Database   |
           +-------------------+               +-------------------+
```

### Event Payload Contracts

All event bus communications must be typed and wrapped inside an envelope structure specifying metadata:

```typescript
interface EventEnvelope<T> {
  eventId: string;          // Unique UUIDv4
  eventType: string;        // E.g., "COUNCIL_EVAL_COMPLETE", "RISK_ALERT"
  source: string;           // Publisher component identifier
  timestamp: string;        // ISO 8601 UTC string
  payload: T;               // Strongly-typed payload content
  schemaVersion: string;    // Semantic version of payload schema
}
```

#### Specialist Event Output Payload Schema (`COUNCIL_EVAL_COMPLETE`):
```json
{
  "eventId": "e938f9b2-38d2-4412-a12f-9cb4812bc852",
  "eventType": "COUNCIL_EVAL_COMPLETE",
  "source": "council.technical_agent",
  "timestamp": "2026-07-10T14:30:00.125Z",
  "payload": {
    "agent_name": "technical_agent",
    "symbol": "BTC/USDT",
    "direction": "BULLISH",
    "confidence": 85.5,
    "score": 0.85,
    "reasoning": [
      "EMA 20/50 crossover confirmed on 1H timeframe.",
      "Volume breakout exceeded 20-period moving average by 1.8x."
    ],
    "data_points": {
      "ema_20": 64230.5,
      "ema_50": 63980.2,
      "volume_ratio": 1.82,
      "rsi_14": 58.4
    },
    "latency_ms": 14.5
  },
  "schemaVersion": "1.2.0"
}
```

---

## 6. Decision Pipeline

Every potential transaction progresses through an orchestrated 11-stage chronological validation pipeline. Each stage is strictly sequential, and any failure or negative assessment triggers instant termination, protecting capital.

```
+-------------+      +--------------------+      +------------------+      +--------------------+
| 1. Market   | ---> | 2. Feature         | ---> | 3. Specialist    | ---> | 4. Evidence        |
|    Data     |      |    Extraction      |      |    Agents        |      |    Collection      |
+-------------+      +--------------------+      +------------------+      +--------------------+
                                                                                      |
                                                                                      v
+-------------+      +--------------------+      +------------------+      +--------------------+
| 8. Risk     | <--- | 7. Consensus       | <--- | 6. Conflict      | <--- | 5. Confidence      |
|    Engine   |      |    Engine          |      |    Engine        |      |    Engine          |
+-------------+      +--------------------+      +------------------+      +--------------------+
       |
       v
+-------------+      +--------------------+      +------------------+
| 9. Portfolio| ---> | 10. Final Decision | ---> | 11. Explanation &|
|    Engine   |      |     (Human Gate)   |      |     DB Storage   |
+-------------+      +--------------------+      +------------------+
```

### Chronological Processing Stages

1.  **Market Data Ingestion**: The system continuously captures tick-by-tick orderbook updates, OHLCV bars, on-chain movements, and sentiment streams via exchange WebSockets and REST pipelines.
2.  **Feature Extraction**: Calculates core indicators (EMA, RSI, ATR, liquidity profiles) and normalizes input data formats.
3.  **Specialist Agent Evaluation**: Coordinator invokes registered agents simultaneously. Each agent runs its isolated inference/evaluation logic on the extracted features.
4.  **Evidence Collection**: Dispatched agent outputs are parsed by the `EvidenceParser` and registered in the `EvidenceRegistry` as discrete `EvidenceItem` models.
5.  **Confidence Calculation**: Supporting and contradicting evidence packages are passed to the Confidence Engine to calculate absolute decision confidence ($C$) and overall evidence strength ($S$).
6.  **Conflict Detection**: Evidence pairs are scanned for behavioral contradictions (e.g., price trending up but whales heavily unloading). If detected, severity is scored and flagged.
7.  **Consensus Aggregation**: Applies weighted voting across all active agents. If consensus score meets the threshold ($S_{\text{consensus}} \geq 85.0$), it passes to risk checks.
8.  **Risk Engine Validation**: Validates the consensus decision against real-time safety thresholds (max drawdown, asset beta constraints, extreme volatility block).
9.  **Portfolio Context Assembly**: Verifies size limitations, correlation overlap across open positions, and current cash balances to output exact position sizing.
10. **Final Decision State Transition**:
    *   *In Development/Test/Paper*: Execution occurs automatically if parameters pass.
    *   *In Live Production*: Suspends transaction and registers a pending authorization ticket on the "Command Deck" requiring the Founder's cryptographic fingerprint or click consent.
11. **Explanation & Storage**: Explainer converts the complete internal pipeline state into a clear natural language reasoning report. The entire evidence trace is serialized and persisted inside `test_elite.db` for performance feedback.

---

## 7. Evidence Engine

The **Evidence Engine** represents the core data extraction and validation pipeline. Its job is to ingest unstructured agent payloads, extract standardized data points, and establish immutable source lineages.

```
                 +-----------------------------------------+
                 |              Evidence Engine            |
                 +-------------------+---------------------+
                                     |
           +-------------------------+-------------------------+
           |                         |                         |
+----------v----------+   +----------v----------+   +----------v----------+
|  Evidence Registry  |   |   Evidence Parsers  |   |   Source Tracer     |
| (Active validation) |   |  (Extract fields)   |   | (Version & Origin)  |
+---------------------+   +---------------------+   +---------------------+
```

### Components
*   **Evidence Registry**: Acts as an in-memory repository for active evaluations, ensuring evidence items pass structure validation before they are parsed downstream.
*   **Evidence Parsers**: Dedicated converters that digest custom data payloads from varied sources and output a standardized `EvidenceItem`. For instance, standardizing on-chain transaction metadata from Ethereum and Solana into a single schema.
*   **Source Tracer**: Attaches version numbers and exact execution hashes to ensure that the user can track an agent's advice back to a specific Git release or database state.

### Traceability Mapping Architecture

Every `EvidenceItem` maps back to an explicit code file and model parameters:

```
[Evidence ID: ev_9a8c1f] ---> [Origin: council.technical_agent] ---> [Indicator File: features/indicators.py]
                                                                        |
                                                                        v
                                                                   [Code Commit: sha_7770f92]
```

---

## 8. Confidence Engine

Elite's confidence formulation mathematically measures both **Directional Consensus Intensity** and **Evidence Coverage Diversity**. It rejects arbitrary weights in favor of a clear, explainable scoring structure.

```
                                  +---------------------------------------+
                                  |            Confidence Engine          |
                                  +-------------------+-------------------+
                                                      |
                  +-----------------------------------+-----------------------------------+
                  |                                   |                                   |
+-----------------v-----------------+ +-----------------v-----------------+ +-----------------v-----------------+
|   Directional Confidence (C)     | |      Evidence Strength (S)      | |      Explainability Index (E)     |
| Support vs. Contradict Intensity  | |     Max vs. Actual Strength     | |    Coverage, Diversity, & Time    |
+-----------------------------------+ +-----------------------------------+ +-----------------------------------+
```

### Mathematical Formulations

#### 1. Directional Confidence ($C$)
Measures the ratio of supporting evidence weight to contradicting evidence weight, scaled by confidence intensity:

$$C = \frac{\sum (W_{\text{sup}} \times \text{ev\_conf}_{\text{sup}} \times \mu_{\text{sup}}) - \sum (W_{\text{contra}} \times \text{ev\_conf}_{\text{contra}} \times \mu_{\text{contra}})}{\sum (W_{\text{sup}} \times \text{ev\_conf}_{\text{sup}} \times \mu_{\text{sup}}) + \sum (W_{\text{contra}} \times \text{ev\_conf}_{\text{contra}} \times \mu_{\text{contra}})}$$

*   Normalized Output: The confidence is mapped to a $[0, 100]$ range:
    $$\text{Confidence}_{\text{final}} = \max\left(0.0, \min\left(100.0, \left(C + 1.0\right) \times 50.0\right)\right)$$
*   **Weights Definitions**:
    *   $\mu_{\text{sup}} = 1.0$ (Supporting multiplier weight)
    *   $\mu_{\text{contra}} = 1.2$ (Contradicting multiplier weight—we penalize contradiction more heavily to protect capital)
    *   $W_{\text{sup}}, W_{\text{contra}}$: Engine significance weights (e.g., `risk_engine = 1.2`, `portfolio = 0.8`).
    *   $\text{ev\_conf}$: Confidence score reported by individual agents $[0.0, 1.0]$.

#### 2. Evidence Strength ($S$)
Measures the physical volume of supportive evidence compared to the maximum possible evidence:

$$S = \left( \frac{\sum (W_{\text{sup}} \times \text{ev\_conf}_{\text{sup}} \times \text{Severity}_{\text{weight}})}{\sum (W_{\text{sup}} \times \text{Severity}_{\text{weight}})} \right) \times 100.0$$

Where $\text{Severity}_{\text{weight}}$ is derived from:
$$\text{Severity}_{\text{weight}} = \begin{cases} 2.0 & \text{CRITICAL} \\ 1.5 & \text{HIGH} \\ 1.0 & \text{MEDIUM} \\ 0.5 & \text{LOW} \end{cases}$$

#### 3. Explainability Index ($E$)
Measures the qualitative structure of the decision trace:

$$E = \left( 0.35 \times \text{Cov} + 0.30 \times \text{Div} + 0.20 \times \text{Time} + 0.15 \times \text{Contra}_{\text{vis}} \right) \times 100.0$$

*   $\text{Cov}$ (Coverage): Ratio of active evidence pieces to standard threshold: $\min(1.0, N_{\text{items}} / 5.0)$
*   $\text{Div}$ (Diversity): Ratio of unique active engines: $\min(1.0, N_{\text{engines}} / 3.0)$
*   $\text{Time}$ (Timeline density): Measures temporal coverage of data ticks: $\min(1.0, N_{\text{ticks}} / 3.0)$
*   $\text{Contra}_{\text{vis}}$ (Contradictory visibility): A binary flag set to $1.0$ if contradictory items were explicitly checked and processed, and $0.5$ otherwise.

---

## 9. Conflict Engine

Disagreements within a council of specialists are normal. The **Conflict Engine** identifies, quantifies, and attempts to resolve these disagreements using formal structural logic.

### Disagreement Detection Matrix

The Conflict Engine continuously evaluates combinations of supporting and contradicting engines based on active rules:

```
                      +-------------------+
                      |   Active Agents   |
                      +---------+---------+
                                |
               +----------------+----------------+
               |                                 |
+--------------v---------------+  +--------------v---------------+
|    Supporting Evidences      |  |    Contradicting Evidences   |
| [technical_agent: "BULLISH"] |  |   [news_agent: "BEARISH"]    |
+--------------+---------------+  +--------------+---------------+
               |                                 |
               +----------------+----------------+
                                |
                                v
               +---------------------------------+
               |         Conflict Pair           |
               |     "Technical vs. News"        |
               +---------------------------------+
```

### Severity Calculation Logic
Conflict severity is graded as **LOW**, **MEDIUM**, **HIGH**, or **CRITICAL** based on:
1.  **Agent Weight Synergy**: High-weight agents in conflict elevate severity.
2.  **Specific Pair Multipliers**: Conflict between `risk_engine` and `scanner` is immediately scaled to **CRITICAL** if the underlying risk metric is **HIGH** or **MEDIUM**.

### Resolution Rules Matrix

| Conflicting Pair | Primary Action | Default Outcome | Resolution Pathway |
|---|---|---|---|
| **Risk vs. Scanner** | Veto | Terminate Execution | Discard signal immediately. |
| **Council vs. Scanner** | Scale Sizing | Reduce exposure by 50% | Proceed only if Technical and Macro agents agree. |
| **Portfolio vs. Decision** | Exposure Clamp | Limit exposure to 1% of equity | Force maximum portfolio alignment constraint. |
| **Market vs. Scanner** | Delay Entry | Wait for next cycle | Re-evaluate in 60 seconds. |

---

## 10. Consensus Engine

Consensus represents the unified voice of the platform's AI brains. The consensus pipeline evaluates votes from all active agents, maps them against prioritization weights, and makes a unified decision.

```
                 +-----------------------------------------+
                 |            Consensus Engine             |
                 +-------------------+---------------------+
                                     |
           +-------------------------+-------------------------+
           |                         |                         |
+----------v----------+   +----------v----------+   +----------v----------+
|  Weighted Voting    |   | Threshold Checker   |   |   Fallback Logic    |
| (Calculate V_score) |   | (Compare vs. 85.0)  |   | (Safe PASS default) |
+---------------------+   +---------------------+   +---------------------+
```

### Aggregation & Vote Formulas
For each prospective symbol, the overall consensus score ($V_{\text{consensus}}$) is calculated using agent directional weights:

$$V_{\text{consensus}} = \frac{\sum_{i=1}^{M} W_i \times D_i \times C_i}{\sum_{i=1}^{M} W_i \times C_i}$$

Where:
*   $W_i$: Default configuration weight of agent $i$ (e.g., Technical = 1.0, Risk = 1.5).
*   $C_i$: Confidence output by agent $i$ (expressed as $[0.0, 100.0]$).
*   $D_i$: Direction factor mapping:
    $$D_i = \begin{cases} 1.0 & \text{DIRECTION\_BULLISH} \\ -1.0 & \text{DIRECTION\_BEARISH} \\ 0.0 & \text{DIRECTION\_NEUTRAL / DIRECTION\_PASS} \end{cases}$$

### Consensus Threshold Rules
*   **STRONG BUY Threshold**: $V_{\text{consensus}} \geq 85.0$
*   **STRONG SELL Threshold**: $V_{\text{consensus}} \leq -85.0$
*   **NO CONSENSUS**: $-85.0 < V_{\text{consensus}} < 85.0$ (Platform executes `DIRECTION_PASS` state)

---

## 11. Decision Engine

The **Decision Engine** serves as the central state machine orchestrating the operational flow. It governs state changes from ingestion to completion, ensuring the system remains responsive, stable, and completely safe under all conditions.

### Comprehensive State Transition Machine

```
                      +-------------------+
                      |     INITIATED     |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |     EVALUATING    |
                      +---------+---------+
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
   +-------------------+                 +-------------------+
   |     CONFLICTED    |                 |      APPROVED     |
   | (Halt execution)  |                 +---------+---------+
   +-------------------+                           |
                                                   v
                                         +-------------------+
                                         |    RISK_BLOCKED   |
                                         | (Emergency Halt)  |
                                         +---------+---------+
                                                   |
                                                   v
                                         +-------------------+
                                         |     EXECUTED      |
                                         |  (Paper or Live)  |
                                         +-------------------+
```

### State Definitions & Guards

*   **INITIATED**: Signal received from the scanner or API. Guard: Ingestion contract must validate.
*   **EVALUATING**: Coordinator evaluates all registered specialists. Guard: Every agent must complete execution within 1500ms or trigger an isolated timeout report.
*   **CONFLICTED**: High-severity conflict detected by the Conflict Engine. Guard: Disables order routing; returns detailed alert trace to terminal console.
*   **APPROVED**: Consensus score exceeds the threshold ($V_{\text{consensus}} \geq 85.0$). Guard: Requires validation by Risk Engine.
*   **RISK_BLOCKED**: Risk evaluation fails one or more hard safety guidelines. Guard: Triggers an alert event on the user dashboard.
*   **EXECUTED**: Position generated inside paper or live trading layer. Guard: Order filled event returned from the trade executor.

---

## 12. Trust & Explainability

Transparency is the foundation of EDE. To foster trust, the system implements natural language generator utilities that dynamically convert complex mathematical score states into human-readable narratives.

### Explainability Matrix Generation Template

```
===================================================================================
DECISION REPORT: BTC/USDT [STRONG BUY] - Confidence: 89.4% (Quality: STRONG)
===================================================================================
RATIONALE:
The platform recommends a STRONG BUY for BTC/USDT. This is supported by 4 of 6 active
agents, representing a total supporting evidence strength of 92.5%.

COUNCIL DEBATE SUMMARY:
-----------------------------------------------------------------------------------
Agent             Direction       Weight    Confidence    Key Findings
-----------------------------------------------------------------------------------
TechnicalAgent    BULLISH         1.0       95.0%         EMA crossover confirmed.
WhaleAgent        BULLISH         0.6       85.0%         Inflow of $12M to cold wallets.
MacroAgent        BULLISH         0.5       70.0%         Funding rates near historical lows.
PortfolioAgent    NEUTRAL         1.0       100.0%        Within current exposure limits.
NewsAgent         BEARISH         0.8       55.0%         FUD detected on crypto forums.
RiskAgent         BULLISH         1.5       90.0%         Volatility within stable bounds.

CONFLICTS ENCOUNTERED:
- [MEDIUM] Technical vs News: Price action is bullish, but News Agent detected negative
  retail market sentiment. Resolve: Proceeding due to high-conviction whale support.

EVIDENCE BLOCK ATTESTATION:
- Evidence UUID: ev_7a9c2f | Source: Binance API v3 | Checked by: Risk Engine v2.1
===================================================================================
```

---

## 13. Memory & Learning

The decision logic is not static. EDE uses past performance context to calibrate its scoring models.

```
                                +---------------------------+
                                |  Historical Performance   |
                                |     Feedback Loop         |
                                +-------------+-------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
           +---------v---------+                             +---------v---------+
           |     Database      |                             |   Decision Engine |
           |  SQLite/Postgres  |                             |   Evaluation Loop |
           |                   |                             |                   |
           | Realized PnL      |                             | Agent Performance |
           | Drawdowns         |                             | Calibration       |
           | Holding Time      |                             | Weight Adjustments|
           +-------------------+                             +-------------------+
```

### Self-Calibration & Weight Adaptation Formula
The weight ($W_i$) of each specialist agent is automatically calibrated at the end of every trading session (defined as 7 days or after 100 closed trades) based on its realized accuracy ($A_i$):

$$W_i^{(t+1)} = W_i^{(t)} \times \left(1.0 + \eta \times \frac{A_i - \bar{A}}{\bar{A}}\right)$$

Where:
*   $\eta$: Learning rate parameter (default = `0.05`).
*   $A_i$: Realized precision accuracy of agent $i$ (percentage of signals matching final realized PnL direction).
*   $\bar{A}$: Mean accuracy of all active council specialists combined.
*   Guards: Adjusted weights are hard-capped to keep them within predictable boundaries:
    $$0.5 \leq W_i \leq 2.0$$

---

## 14. Risk Integration

Capital preservation is prioritized over directional yield. The Decision Engine integrates directly with the **Risk Manager** to enforce system safety boundaries.

```
                              +------------------------+
                              |      Risk Manager      |
                              +-----------+------------+
                                          |
                +-------------------------+-------------------------+
                |                                                   |
      +---------v---------+                               +---------v---------+
      |  Hard Risk Gates  |                               |    Soft Warnings  |
      | (Immediate Veto)  |                               | (Sizing Clamps)   |
      +-------------------+                               +-------------------+
```

### Safety Rules Matrix

| Rule ID | Metric Name | Target Threshold | Active Action | Scope |
|---|---|---|---|---|
| **R-01** | Max Daily Loss (MDL) | $2.5\%$ of total equity | Stop all active execution | Global |
| **R-02** | Volatility Max | ATR (14) $\geq 15.0\%$ of asset price | Discard incoming buy signal | Asset-specific |
| **R-03** | Max Drawdown Limit | $10.0\%$ peak-to-trough | Terminate paper & live loops | Global |
| **R-04** | Liquidity Wall Gap | Bid/Ask spread $\geq 0.50\%$ | Restrict order entry to post-only | Asset-specific |
| **R-05** | Leverage Ceiling | $3.0\times$ leverage | Force leverage deleveraging cascade | Account-specific |

---

## 15. Portfolio Integration

The **Portfolio Engine** ensures that independent asset transactions are executed in a coordinated, well-balanced portfolio context.

```
+----------------------------+
| Proposed Asset Execution   |
+-------------+--------------+
              |
              v
+----------------------------+
|  Portfolio Correlation Gap | --- [If correlation >= 0.75] ---> Discard signal
+-------------+--------------+
              |
              v
+----------------------------+
| Asset Sizing & Allocation  |
+----------------------------+
```

### Sizing Adjustment Engine
Before signal submission, the Portfolio Engine determines the optimal position size ($P_{\text{size}}$) by combining risk metrics, Kelly Criterion, and asset-specific correlation metrics:

$$P_{\text{size}} = \text{Base\_Size} \times (1.0 - \text{Corr}_{\text{max}}) \times \frac{\text{Cash}_{\text{available}}}{\text{Portfolio}_{\text{equity}}}$$

Where:
*   $\text{Corr}_{\text{max}}$: The maximum correlation index of the prospective asset against all active open positions ($[-1.0, 1.0]$). If $\text{Corr}_{\text{max}} \geq 0.75$, the transaction is blocked.
*   $\text{Base\_Size}$: Calculated position target based on localized ATR volatility profiles.

---

## 16. Event Flow

Below is the complete architectural trace mapping the event flow from market data ingestion to final execution.

### Execution Event Flow Sequence

```
+--------+          +-----------+          +---------+          +-------------+          +---------+          +----------+
| Market |          | Indicator |          | Council |          | Consensus / |          |  Risk   |          |  Paper / |
| Source |          | Pipeline  |          | Agents  |          | Confidence  |          | Manager |          | Executor |
+----+---+          +-----+-----+          +----+----+          +------+------+          +----+----+          +----+-----+
     |                    |                     |                      |                      |                    |
     | [Raw Ingest]       |                     |                      |                      |                    |
     |------------------->|                     |                      |                      |                    |
     |                    | [Extract Features]  |                      |                      |                    |
     |                    |-------------------->|                      |                      |                    |
     |                    |                     | [Evaluate Signals]   |                      |                    |
     |                    |                     |--------------------->|                      |                    |
     |                    |                     |                      | [Calculate Cons.]    |                      |
     |                    |                     |                      |--------------------->|                    |
     |                    |                     |                      |                      | [Validate Rules]   |
     |                    |                     |                      |                      |------------------->|
     |                    |                     |                      |                      |                    | [Execute]
     |                    |                     |                      |                      |                    |--------+
     |                    |                     |                      |                      |                    |        |
     |                    |                     |                      |                      |                    |<-------+
     |                    |                     |                      |                      |                    | [Success Event]
     |                    |                     |<-----------------------------------------------------------------|
```

---

## 17. Service Architecture

The service hierarchy is structured as a clean decoupled dependency graph, written with FastAPI router boundaries in the web-delivery layer.

```
          +-------------------------------------------------------------+
          |                      FastAPI Web Layer                      |
          |       (Main API Entry point, Router Integrations)           |
          +------------------------------+------------------------------+
                                         |
          +------------------------------v------------------------------+
          |                     Coordinator Service                     |
          |           (Orchestrates evaluate, feeds endpoints)          |
          +------------------------------+------------------------------+
                                         |
          +------------------------------v------------------------------+
          |                       Decision Engine                       |
          |     (State transitions, Event loops, Consensus evaluation)  |
          +----------+-------------------+-------------------+----------+
                     |                   |                   |
          +----------v----------+ +------v------+ +----------v----------+
          |   Evidence Engine   | | Risk Engine | |  Portfolio Engine  |
          |  (Traces & Parsing) | | (Hard veto) | | (Allocation limits)|
          +---------------------+ +-------------+ +---------------------+
```

### Dependency Injection Pattern
Services are instantiated once at application startup (`api/main.py`) and injected into path operations via Starlette's clean `Depends` wrapper patterns:

```python
# Architecture Blueprint: Dependency Injection Pattern
async def get_coordinator() -> CoordinatorService:
    return app.state.coordinator_service
```

This pattern simplifies unit testing by allowing developers to mock the core coordinator engine with isolated mock instances.

---

## 18. Data Contracts

The fundamental data transfer structures are strictly typed using Python's standard `dataclasses` framework.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List

@dataclass(frozen=True)
class CodeTraceContract:
    file_path: str
    class_name: str
    method_name: str
    module_version: str
    git_commit_sha: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "class_name": self.class_name,
            "method_name": self.method_name,
            "module_version": self.module_version,
            "git_commit_sha": self.git_commit_sha,
        }

@dataclass(frozen=True)
class StandardEvidenceContract:
    id: str
    title: str
    description: str
    engine: str
    category: str
    severity: str = "MEDIUM"
    confidence: float = 0.0
    weight: float = 1.0
    supports_decision: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_trace: Optional[CodeTraceContract] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "engine": self.engine,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "weight": self.weight,
            "supports_decision": self.supports_decision,
            "metadata": self.metadata,
            "source_trace": self.source_trace.to_dict() if self.source_trace else None,
            "timestamp": self.timestamp,
        }
```

---

## 19. JSON Schemas

To ensure clean interoperability between the Python backend and the React frontend, all event telemetry and state objects adhere to strict JSON Schemas.

### 1. Specialist Agent Output Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentReport",
  "type": "object",
  "properties": {
    "agent_name": { "type": "string" },
    "symbol": { "type": "string" },
    "direction": { "type": "string", "enum": ["BULLISH", "BEARISH", "NEUTRAL", "PASS"] },
    "confidence": { "type": "number", "minimum": 0.0, "maximum": 100.0 },
    "score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "reasoning": {
      "type": "array",
      "items": { "type": "string" }
    },
    "data_points": { "type": "object" },
    "latency_ms": { "type": "number" },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["agent_name", "symbol", "direction", "confidence", "score", "reasoning", "timestamp"]
}
```

### 2. Final Decision Payload Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FinalDecisionReport",
  "type": "object",
  "properties": {
    "decision_id": { "type": "string" },
    "symbol": { "type": "string" },
    "recommendation": { "type": "string", "enum": ["STRONG_BUY", "STRONG_SELL", "NO_CONSENSUS"] },
    "decision_confidence": { "type": "number", "minimum": 0.0, "maximum": 100.0 },
    "evidence_strength": { "type": "number" },
    "explainability": { "type": "number" },
    "decision_quality": { "type": "string", "enum": ["STRONG", "MODERATE", "WEAK", "INSUFFICIENT"] },
    "supporting_evidence": {
      "type": "array",
      "items": { "$ref": "#/$defs/EvidenceItem" }
    },
    "contradicting_evidence": {
      "type": "array",
      "items": { "$ref": "#/$defs/EvidenceItem" }
    },
    "conflicts": {
      "type": "array",
      "items": { "$ref": "#/$defs/Conflict" }
    },
    "created_at": { "type": "string", "format": "date-time" }
  },
  "required": ["decision_id", "symbol", "recommendation", "decision_confidence", "decision_quality", "created_at"],
  "$defs": {
    "EvidenceItem": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "engine": { "type": "string" },
        "severity": { "type": "string" },
        "confidence": { "type": "number" }
      },
      "required": ["id", "title", "engine", "severity", "confidence"]
    },
    "Conflict": {
      "type": "object",
      "properties": {
        "pair": { "type": "string" },
        "severity": { "type": "string" },
        "description": { "type": "string" }
      },
      "required": ["pair", "severity", "description"]
    }
  }
}
```

---

## 20. API Contracts

The Decision Intelligence layer exposes structured REST and real-time WebSocket interfaces to support advanced front-end command dashboards.

### Endpoint Matrix

| Method | Route | Description | Query Parameters | Response Structure |
|---|---|---|---|---|
| **GET** | `/api/v1/decision/latest` | Fetches the most recent decision intelligence state | `symbol` (Optional) | `EvidenceReport` JSON |
| **GET** | `/api/v1/decision/history` | Returns historical decisions | `limit` (int, default=10) | List of `EvidenceReport` |
| **GET** | `/api/v1/decision/{id}/timeline` | Returns timeline progression logs for a decision | None required | List of timeline events |
| **GET** | `/api/v1/health/ai` | Returns connection status and latencies for all AI layers | None required | Unified telemetry state JSON |

---

## 21. Error Handling

To achieve the desired reliability targets, the AI subsystem isolates errors to prevent cascading failures.

```
                      +-------------------+
                      |   Invoke Agent    |
                      +---------+---------+
                                |
             +------------------+------------------+
             | (Within 1500ms)                     | (Times out or throws error)
             v                                     v
   +-------------------+                 +-------------------+
   |   Return Report   |                 |   Return Isolated |
   |                   |                 |   Graceful PASS   |
   +-------------------+                 +-------------------+
```

### Graded Degradation Protocol
1.  **Specialist Agent Timeout Isolation**: If any single agent's execution exceeds a strict threshold (`1500ms`), the Coordinator cancels its active thread or coroutine task. The system generates a fallback report with `DIRECTION_PASS` and `0.0` confidence, preventing slow integrations from lagging the core system.
2.  **Schema Failure Fallback**: If an agent returns an improperly typed payload, the `BaseAgent` validation wrapper intercepts the result and emits a `DIRECTION_PASS` report.
3.  **Default-Deny Execution state**: In the event of system-wide anomalies (e.g., more than three agents returning execution errors during a single evaluation tick), the consensus state immediately defaults to `NO_CONSENSUS`, terminating downstream order pathways.

---

## 22. Monitoring

Continuous evaluation requires precise metrics tracking. EDE records high-fidelity telemetry metrics to monitor AI health.

### Core Telemetry KPIs

| KPI Metric | Target Threshold | Warning Threshold | Monitoring Action |
|---|---|---|---|
| **Agent Latency (Technical)** | $\leq 50$ms | $\geq 150$ms | Trigger performance profiling metrics |
| **Agent Latency (On-chain/Whale)** | $\leq 500$ms | $\geq 1500$ms | Log slow database read warnings |
| **Overall Consensus Time** | $\leq 200$ms | $\geq 1000$ms | Alert developer terminal console |
| **Subsystem Error Rate** | $\leq 0.01\%$ | $\geq 1.0\%$ | Halt automated execution immediately |
| **Data Freshness Drift** | $\leq 3000$ms | $\geq 10000$ms | Reset active network WebSocket connections |

---

## 23. Logging

Log outputs follow structured patterns to facilitate rapid debugging and automated parsing by log analysis tools (e.g., Elastic Stack, Datadog).

```json
{"timestamp": "2026-07-10T14:30:00.152Z", "level": "INFO", "component": "decision.evidence_engine", "message": "Evidence report successfully built.", "decision_id": "ev_8b1c2e", "symbol": "BTC/USDT", "metrics": {"confidence": 89.4, "strength": 92.5, "quality": "STRONG"}}
```

```json
{"timestamp": "2026-07-10T14:30:00.165Z", "level": "WARNING", "component": "decision.conflict_detector", "message": "Medium severity conflict identified during evaluation.", "decision_id": "ev_8b1c2e", "conflict": {"pair": "Technical vs News", "severity": "MEDIUM"}}
```

```json
{"timestamp": "2026-07-10T14:30:01.002Z", "level": "ERROR", "component": "council.whale_agent", "message": "On-chain provider WebSocket timed out during query.", "elapsed_ms": 1501.2, "fallback_applied": "DIRECTION_PASS"}
```

---

## 24. Testing Strategy

The AI Decision layer mandates continuous quality assurance checks to maintain robust performance under evolving market regimes.

```
+-----------------------------------------------------------------------------------+
|                            EDE TEST DEPLOYMENT CYCLE                              |
|                                                                                   |
|  [Statistical Mocking] ---> [Deterministic Math Verification] ---> [Regression]  |
+-----------------------------------------------------------------------------------+
```

### Core Testing Pillars
1.  **Deterministic Evaluation Math Validation**: Unit tests verifying `calculate_confidence` must validate correctness down to precise decimals using mock inputs for supporting and contradicting arrays.
2.  **Telemetry Mocking**: Mocks simulate slow agent connections, validating that the Coordinator enforces the strict 1500ms timeout threshold and downgrades gracefully without throwing unhandled exceptions.
3.  **Regime Simulation Checks**: Automated regression scripts replay specific historical regimes (e.g., May 2021 market sell-off) to confirm that the Consensus and Conflict engines consistently block entries under highly volatile conditions.

---

## 25. Future Expansion Rules

The platform architecture is built to evolve. Developers must follow these guidelines to ensure seamless future expansion.

### Rules for Adding a New Agent
1.  **Subclass standard `BaseAgent`**: Place the implementation code within a dedicated file in the `council/` directory.
2.  **Enforce data contract standards**: Ensure the `evaluate` function strictly returns an `AgentReport` dataclass.
3.  **Registry update**: Declare the class and assign its default weight inside `council/__init__.py`.
4.  **Define parsing adapters**: Add custom mapping rules inside `decision/evidence/parser.py` to support standard parsing of custom data points.

### Scaling to Multi-Asset Ecosystems
*   **Decoupled asset contexts**: Avoid hardcoding BTC/ETH assumptions. The `BaseAgent` evaluate interface requires the active `symbol` query parameter to dynamically adapt parameter logic (e.g., scaling volume thresholds relative to the asset class).

### ML-Driven Consensus Tuning
*   **Weight calibration safety limits**: While automated feedback algorithms adjust individual agent weights ($W_i$), the core system configuration must enforce hard limits ($0.5 \leq W_i \leq 2.0$) to prevent runaway optimization loops from skewing the consensus math.

---
*End of Specification — Elite Platform AI Architecture Bible V1.0*
