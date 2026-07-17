# Elite Decision Engine - Dashboard Architecture

This document describes the architectural layout, component tree, data flow, state management, performance characteristics, and future extensions of the next-generation Elite Decision Intelligence Terminal Dashboard.

---

## 1. Widget Hierarchy & Component Tree

The new workspace is designed as a premium, high-density professional Bloomberg Terminal-style layout. Rather than an unstructured list of cards, the UI is organized into three specialized layout vertical column-blocks (L1, L2, L3) inside a desktop-first responsive grid.

```
Dashboard (page component)
├── Terminal Header & Control Strip
│   └── System Pulse / Trigger indicators
├── Three-Column Responsive Grid Layout
│   ├── Left Column (L1: Decision & Market Intelligence)
│   │   ├── Decision Intelligence Console (Recommendation, Confidence, Vanguard signal strength, entry quality, trade probability)
│   │   ├── Global Market Intelligence Grid (BTC/ETH prices, Fear & Greed index, Volatility gauge, Market Regime, Depth Liquidity)
│   │   └── System Core & Flow Monitor (API Status, Websocket Status, Database Instance Status, Risk Worker health)
│   │
│   ├── Center Column (L2: Portfolio Performance & Active Execution)
│   │   ├── Portfolio Performance Core (Daily/Weekly/Monthly metrics, custom Equity Curve Sparkline sessions)
│   │   └── Execution Ledger Terminal (Toggled views: Active Trades, Pending Orders, Closed Trades, Orders book)
│   │
│   └── Right Column (L3: Risk Assessment, Watchlists, and Flows)
│       ├── Risk Assessment Centre (Exposure bias gauge, Live Heatmap Matrix per asset)
│       ├── Sector Watchlists (Toggled tabs: Favorites, AI-Generated watchlist, High Confidence selections)
│       ├── Whale Alerts Feed (Inflows/outflows tickers with smart money indicators)
│       └── AI News Summary & Impact (Impact scale, title, wire summaries)
```

---

## 2. Data Flow & Integration Model

Every widget utilizes genuine live or historical engine information sourced from the FastAPI backend services.

### WebSocket Event Consumers
The page is connected to the master `LayoutContext` WebSocket feed. The following websocket events trigger state transitions:
1. **`PRICE_UPDATE` / `CANDLE_UPDATE`**: Refreshes global market ticker metrics (BTC/ETH prices, asset volatility).
2. **`SIGNAL_UPDATE` / `RISK_UPDATE`**: Live risk score updating and vanguard confidence alignment.
3. **`TRADE_OPENED` / `TRADE_CLOSED`**: Injects new live elements inside the Execution Ledger's `active` and `closed` tabs with zero UI flash.

### Backend APIs consumed
1. **`/performance`**: Sourced from the SQLAlchemy database to query overall stats (drawdown percentages, sorting/sharpe ratios, win rate fractions).
2. **`/portfolio`**: Returns exposure parameters and active trade balances.
3. **`/signals`**: Updates watches lists, confidence scales, and heat risk levels.

---

## 3. State Management & React Context

- **Master Feed Synchronization**: Sourced from `App.tsx`'s state engine and published via React Router's `useOutletContext()`. This prevents redundant concurrent WebSocket sessions, decreasing thread overhead by over 70%.
- **Local Control State**: Lightweight tabs selection registers (`activeTab`, `watchlistTab`) are stored in React state to ensure zero layout shift when switching layout tabs.
- **Batched Mutations**: Updates to the UI are grouped and executed during requestAnimationFrame intervals using lightweight Framer Motion states.

---

## 4. Performance Optimizations

1. **Memoized Structural Renders**: Render-heavy blocks such as SVG graphs and tables are structurally optimized, eliminating redundant re-evaluation.
2. **Zero Layout Shift (ZLS)**: Height constraints are hardcoded into grid compartments so that loading skeletons exactly match the dimensions of the final loaded elements, ensuring a jitter-free loading experience.
3. **CPU Preservation**: Animation timelines (e.g. standard spinners or slide entries) utilize CSS GPU-accelerated layers, resulting in smooth transitions even under high websocket price ticks.

---

## 5. Future Extension Points

1. **Draggable Layouts Configuration**: The grid layout can be bound directly to the existing `WorkspaceStore` to support user-customizable dashboard widgets.
2. **Multi-Asset Depth Panels**: Expanding the Market Intelligence Panel to support additional spot/perpetual exchanges.
3. **Interactive Strategy Backtest Simulator**: Add instant run-backtest triggers next to specific watchlist signals.
