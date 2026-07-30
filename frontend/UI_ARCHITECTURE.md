# UI Architecture — Elite Terminal

## Layout Structure

```
┌──────────────────────────────────────────────────┐
│                    Header                         │
│  Branding              WebSocket Status           │
├────────┬──────────────────────────┬───────────────┤
│        │                          │               │
│  Left  │  Center Evidence Surface │    Right      │
│ Sidebar│    (React Router        │ Intelligence  │
│ (w-56) │     Outlet)             │ Panel (w-72)  │
│        │                          │               │
│ Nav:   │  Portfolio               │ AI Summary    │
│ - Brain│  Market                  │ Market Pulse  │
│ - Ollo │  Whale                   │ Intelligence  │
│        │  Risk                    │               │
│        │  News                    │               │
│        │  Scheduler               │               │
│        │  Governance              │               │
├────────┴──────────────────────────┴───────────────┤
│              Status Bar (System Online)           │
└──────────────────────────────────────────────────┘
```

## Component Tree

```
App
├── ThemeProvider (dark mode, density, contrast)
├── AuthProvider
│   └── BrowserRouter
│       ├── /login → LoginPage
│       └── AuthGuard
│           └── Layout
│               ├── Header
│               │   └── ConnectionStatusBadge
│               ├── Sidebar
│               │   └── NavLink (per route)
│               ├── <Outlet> (page content - Center Evidence Surface)
│               └── Right Panel
│                   ├── IntelligencePanel
│                   ├── AI Summary (widget-card)
│                   └── Market Pulse (widget-card)
│
├── Temporary Evidence Surfaces (each wrapped in BrainTransition/Framer Motion)
│   ├── Portfolio (Parietal activation)
│   │   ├── KpiGrid
│   │   ├── DashboardStats
│   │   ├── PnLChart
│   │   ├── OpenTrades / ClosedTrades
│   │   └── PortfolioSummaryCard
│   │
│   ├── Market (Occipital + Frontal activation)
│   │   ├── Category tabs (5)
│   │   ├── Search input
│   │   └── Opportunity cards
│   │
│   ├── Whale (Temporal activation)
│   │   └── On-chain flow & wallets
│   │
│   ├── Risk (Amygdala red pulse)
│   │   └── Exposure levels & limits
│   │
│   ├── News (Hippocampus + Temporal)
│   │   └── NLP sentiment & headlines
│   │
│   ├── Scheduler (Anti-starvation process queue)
│   │   └── Priority scheduler telemetry
│   │
│   ├── Governance (Explicit activation)
│   │   └── Recommendation validation
│   │
│   └── AssetDetail
│       ├── Price badge + header
│       ├── Chart panel
│       ├── Indicators (RSI, EMA, Volume)
│       ├── ExplainableAIPanel
│       ├── DecisionTimeline
│       └── Side widgets (Whale, News, Funding, OI, Liquidity)
│
├── Shared Components
│   ├── ui/ (Button, Badge, Card, Input, Progress, etc.)
│   ├── ai/ (ExplainableAI, Confidence, Whale, News, etc.)
│   ├── charts/ (PriceChart, PnLChart, EquityCurve, etc.)
│   ├── dashboard/ (Widgets, KPIs, Notifications, etc.)
│   ├── layout/ (Header, Sidebar, Topbar, Shell, etc.)
│   ├── signals/ (SignalTable, ScoreCard, etc.)
│   └── trading/ (OrderPanel, ChartPanel, etc.)
│
└── Services
    ├── api/ (21+ endpoint modules)
    ├── websocket/ (Real-time client)
    ├── stores/ (Zustand: ui, terminal, evidence-surface, data)
    └── hooks/ (useWebSocket, useApi, useMediaQuery, etc.)
```

## State Management

| Store | Purpose |
|-------|---------|
| ui-store | Command palette, global search, toasts |
| terminal-store | Current symbol, recent/favorite symbols |
| evidence-surface-store | Temporary evidence surfaces state (active/inactive), focal mode |
| data-store | API data cache |

## Data Flow

1. REST API calls via `apiFetch()` → TanStack Query (10-30s polling)
2. WebSocket events → `App.tsx` → `LayoutContext` → `Outlet` context
3. Scanner data → `/scanner/category/{category}` API → React state
4. Click handler → `terminal-store.setSymbol()` → route navigation

## Cognitive Evidence Surface Interaction Model (Refined)

### 1. Conceptual Shift: From Workspace to Evidence Surface
- **Evidence Over Pages**: Traditional persistent routing pages are discarded. Every visible layout is a temporary **Evidence Surface** generated on-the-fly when an active Cognitive Process produces diagnostic evidence.
- **Visual Manifestation of Reasoning**: The UI does not feel like software where user opens tools. Instead, NEXUS presents visual evidence dynamically based on AI reasoning states.
- **Brain Origin**: All surfaces visually emerge from the central Brain canvas and dissolve back into it. Nothing remains permanently open or independent.

### 2. Brain Anatomy & Cognitive Function Mapping
Animations are driven by Framer Motion and correspond directly to actual backend cognitive AI states:
- **Portfolio** → **Parietal activation**: Spatial and quantitative integration of portfolio health.
- **Market Analysis** → **Occipital + Frontal activation**: Visual token/symbol observation and tactical planning.
- **Whale Intelligence** → **Temporal activation**: Pattern recognition and flow analysis.
- **Risk** → **Amygdala red pulse**: Defensive caution alert triggering system-wide limits.
- **Decision** → **Frontal cortex white bloom**: Executive execution consensus bloom.
- **Learning** → **Hippocampus violet reorganization**: Cognitive knowledge restructuring.
- **Memory Recall** → **Hippocampus + Temporal**: Dual-layer activation fetching episodic decisions.

### 3. Conversation Continuity & Persistence
- **Persistent Conversation**: The natural language conversation timeline is the invariant cognitive trunk of the platform and remains active at all times.
- **Evidence Placement**: Evidence Surfaces appear beside, beneath, or wrap around the conversation layout using non-disruptive, fluid grid adjustments.
- **Seamless Dissolution**: When an Evidence Surface is dismissed or dissolves, the active conversation context persists uninterrupted.
