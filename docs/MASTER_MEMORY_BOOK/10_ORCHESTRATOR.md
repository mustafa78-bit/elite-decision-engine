# Chapter 10: Orchestrator

## ⚙️ The ExecutionLoop Core Coordinator
The operational heartbeat of the NEXUS decision pipeline is the **Execution Loop**, located at `execution/execution_loop.py`. The Execution Loop is an automated background scheduler that coordinates data flow across the entire platform.

### Key Responsibilities:
- Continuously polling the database for raw signals with a status of `"OPEN"`.
- Intercepting active positions to trigger price-monitoring tick loops.
- Driving execution and clearing stale transactions.

---

## 🔁 Continuous Polling & Batch Processing Cycles

The loop operates as a stateful, recurring batch cycle. Below is the internal flow of an `ExecutionLoop` iteration:

```mermaid
graph TD
    Start[Loop Iteration Triggered - Default: Every 10s] --> Poll_Signals[Poll DB for 'OPEN' Signals]
    Poll_Signals --> Signals_Found{Any OPEN Signals?}

    %% Signal pipeline path
    Signals_Found -->|Yes| Fetch_Context[Fetch normalized OHLCV & Indicators via MarketDataService]
    Fetch_Context --> Process_Pipeline[Invoke DecisionPipeline.evaluate_signal]
    Process_Pipeline --> Risk_Check[Invoke RiskEngine & ExecutionGuard]
    Risk_Check --> Risk_Passed{Risk Decision PASS?}

    Risk_Passed -->|Yes| Sizing[Invoke PositionSizingEngine & ATR TPSLEngine]
    Sizing --> Persist_Trade[Create & Persist Trade Model status: OPEN]
    Persist_Trade --> Close_Signal[Update Signal status: CLOSED, approved: True]

    Risk_Passed -->|No| Reject_Signal[Update Signal status: REJECTED, record RejectionReason]

    %% Trade monitoring path (Parallel execution flow)
    Signals_Found -->|No| Poll_Trades[Poll DB for 'OPEN' Trades]
    Reject_Signal --> Poll_Trades
    Close_Signal --> Poll_Trades

    Poll_Trades --> Active_Trades{Any OPEN Trades?}
    Active_Trades -->|Yes| Ticks[Invoke PaperExecutor.monitor_open_trades]
    Ticks --> Match_Price[Compare Live Price to Stop-Loss / Take-Profit targets]
    Match_Price --> Limit_Hit{TP or SL Hit?}

    Limit_Hit -->|Yes| Close_Trade[Update Trade status: CLOSED, record PnL]
    Limit_Hit -->|No| Check_Stale[Apply 7-day Position Timeout]
    Check_Stale --> Timeout_Hit{Timeout Exceeded?}
    Timeout_Hit -->|Yes| Close_Stale[Auto-close Position status: CLOSED, reason: STALE]
    Timeout_Hit -->|No| Sleep[Sleep for interval duration]

    Active_Trades -->|No| Sleep
    Close_Trade --> Sleep
    Close_Stale --> Sleep

    Sleep --> Start
```

### Core Execution Parameters (Configured in `config.py` & `.env`):
- **`POLLING_INTERVAL`**: Defaults to **10 seconds**. Controls how frequently the loop scans for raw signal arrivals and ticks paper positions.
- **`STALE_TRADE_TIMEOUT`**: Defaults to **7 days** (`604800` seconds). Positions open for longer than this duration are automatically liquidated by the engine to free up portfolio capital.
- **`MAX_OPEN_TRADES`**: Defaults to **3**. Dictates the maximum capacity of concurrent active trades the orchestrator can manage.
