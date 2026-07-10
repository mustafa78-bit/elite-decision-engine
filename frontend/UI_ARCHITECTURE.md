# UI Architecture — Elite Terminal

## Layout Structure

```
┌──────────────────────────────────────────────────┐
│                    Header                         │
│  Branding              WebSocket Status           │
├────────┬──────────────────────────┬───────────────┤
│        │                          │               │
│  Left  │    Center Workspace     │    Right      │
│ Sidebar│    (React Router        │ Intelligence  │
│ (w-56) │     Outlet)             │ Panel (w-72)  │
│        │                          │               │
│ Nav:   │  Dashboard              │ AI Summary    │
│ - Dash  │  Scanner               │ Market Pulse  │
│ - Portfolio│  Asset Detail       │ Intelligence  │
│ - Scanner│  Portfolio             │               │
│ - Trades │  Paper Trading         │               │
│ - Signals│  + more...            │               │
│        │                          │               │
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
│               ├── <Outlet> (page content)
│               └── Right Panel
│                   ├── IntelligencePanel
│                   ├── AI Summary (widget-card)
│                   └── Market Pulse (widget-card)
│
├── Pages (each wrapped in PageTransition)
│   ├── Dashboard
│   │   ├── KpiGrid
│   │   ├── DashboardStats
│   │   ├── PnLChart
│   │   ├── OpenTrades / ClosedTrades
│   │   ├── NotificationPanel
│   │   └── PortfolioSummaryCard
│   │
│   ├── Scanner
│   │   ├── Category tabs (5)
│   │   ├── Search input
│   │   └── Opportunity cards
│   │
│   ├── AssetDetail
│   │   ├── Price badge + header
│   │   ├── Chart panel
│   │   ├── Indicators (RSI, EMA, Volume)
│   │   ├── ExplainableAIPanel
│   │   ├── DecisionTimeline
│   │   └── Side widgets (Whale, News, Funding, OI, Liquidity)
│   │
│   └── Profile
│       ├── Avatar + info
│       ├── Account card
│       ├── API Keys card
│       ├── Notification Preferences
│       └── Recent Activity
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
    ├── stores/ (Zustand: ui, terminal, workspace, data)
    └── hooks/ (useWebSocket, useApi, useMediaQuery, etc.)
```

## State Management

| Store | Purpose |
|-------|---------|
| ui-store | Command palette, global search, toasts |
| terminal-store | Current symbol, recent/favorite symbols |
| workspace-store | Panels, fullscreen, focus mode, layouts |
| data-store | API data cache |

## Data Flow

1. REST API calls via `apiFetch()` → TanStack Query (10-30s polling)
2. WebSocket events → `App.tsx` → `LayoutContext` → `Outlet` context
3. Scanner data → `/scanner/category/{category}` API → React state
4. Click handler → `terminal-store.setSymbol()` → route navigation
