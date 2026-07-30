# Chapter 17: Paper Trading

## 🧪 Zero-Risk Market Simulation
The **Paper Trading Engine**, structured under `execution/paper_executor.py` and `execution/paper.py`, provides a zero-risk market simulation environment. By tracking prices and executing orders in memory, the engine allows strategies to be verified against live market conditions without committing capital.

---

## 🔁 The Ticking, Monitoring, and Liquidation Loop

The simulated trade monitoring process is executed as a recurring loop by the `PaperExecutor` class:

```mermaid
graph TD
    Start[Tick Loop Triggered - Default: Every 10s] --> Query_Trades[Query DB for 'OPEN' PaperTrades]
    Query_Trades --> Active_Trades{Any active paper trades?}

    %% Monitoring loop
    Active_Trades -->|Yes| Fetch_Price[Fetch current price via MarketDataService]
    Fetch_Price --> Evaluate_TP{Current Price >= Take Profit Target?}

    Evaluate_TP -->|Yes| Close_TP[Close Position: Status TAKE_PROFIT, record PnL]
    Evaluate_TP -->|No| Evaluate_SL{Current Price <= Stop Loss Target?}

    Evaluate_SL -->|Yes| Close_SL[Close Position: Status STOP_LOSS, record PnL]
    Evaluate_SL -->|No| Evaluate_Stale{Position active > 7 days?}

    Evaluate_Stale -->|Yes| Close_Stale[Close Position: Status CLOSED, reason STALE]
    Evaluate_Stale -->|No| Keep_Open[Maintain active position]

    %% Post-close actions
    Close_TP --> Broadcast[Emit update event to 'trades' & 'notifications' WS rooms]
    Close_SL --> Broadcast
    Close_Stale --> Broadcast

    Broadcast --> Sleep[Sleep for interval duration]
    Active_Trades -->|No| Sleep
    Keep_Open --> Sleep

    Sleep --> Start
```

### Core Execution Safeguards:
- **`Volatility-Based Sizing`**: Scales risk exposures dynamically based on asset volatility (ATR) and macro market regimes, mitigating catastrophic losses on highly volatile instruments.
- **`Automated Take Profit / Stop Loss (TP/SL) Execution`**: Tracks simulated prices in real time, automatically executing stop-loss and take-profit targets to protect simulated balances.
- **`7-Day Capital Preservation Timeout`**: Automatically liquidates any open trade that remains inactive for longer than 7 days, freeing up simulated capital and preventing dead-money drag.
- **`Real-Time Event Broadcasts`**: Automatically serializes and pushes execution updates to active browser clients, keeping HUD widgets synchronized with simulated positions.
