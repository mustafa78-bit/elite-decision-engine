# Architecture Report — Batch 1 (Items 1-80)

## System Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                    ELITE TERMINAL V1                          │
│                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  │
│  │      FRONTEND (React)    │  │      BACKEND (FastAPI)    │  │
│  │                          │  │                          │  │
│  │  ┌────────────────────┐  │  │  API Layer (30+ routes)  │  │
│  │  │  Provider Chain    │  │  │  Market Data             │  │
│  │  │  ┌──────────────┐  │  │  │  Exchange Connectors    │  │
│  │  │  │ ThemeProvider │  │  │  │  Risk Engine            │  │
│  │  │  │ AuthProvider  │  │  │  │  AI Pipeline            │  │
│  │  │  │ QueryClient   │  │  │  │  Memory System          │  │
│  │  │  │ BrowserRouter │  │  │  │  Database (SQLite)      │  │
│  │  │  └──────────────┘  │  │  └──────────────────────────┘  │
│  │  └────────────────────┘  │                               │
│  │  ┌────────────────────┐  │                               │
│  │  │  Component Tree    │  │                               │
│  │  │  Shell             │  │                               │
│  │  │  ├── Sidebar (19)  │  │                               │
│  │  │  ├── Topbar        │  │                               │
│  │  │  ├── CommandPalette│  │                               │
│  │  │  ├── ToastProvider │  │                               │
│  │  │  └── <Outlet />    │  │                               │
│  │  │      ├── Pages (28)│  │                               │
│  │  │      └── Widgets   │  │                               │
│  │  └────────────────────┘  │                               │
│  └──────────────────────────┘                               │
└──────────────────────────────────────────────────────────────┘
```

## Frontend Architecture Detail

### File Layout
```
src/
├── api/                   # REST client (1) + endpoint files (21)
├── components/
│   ├── auth/              # AuthGuard, AuthProvider
│   ├── theme/             # ThemeProvider
│   ├── ui/                # 25 reusable UI components
│   ├── layout/            # Shell, sidebar, topbar, toast, transitions
│   ├── dashboard/         # 38 widget components + registry + builder + analytics
│   ├── trading/           # Symbol search, chart panel, order panel, TV suite
│   ├── ai/                # Chat, signal feed, analysis dashboard
│   ├── workspace/         # Resizable panels, dockable widgets, workspace manager
│   └── performance/       # Lazy load, memoized widget wrappers
├── hooks/                 # useWebSocket, useMediaQuery, TanStack Query hooks
├── lib/                   # Utils, accessibility, websocket hooks
├── pages/                 # 28 page components
├── stores/                # 5 Zustand stores (workspace, terminal, ui, data, preferences)
├── styles/                # tokens.css, globals.css (design system)
├── types/                 # TypeScript type definitions
├── utils/                 # Lazy route configurations
├── websocket/             # WebSocket client with 5 channel functions
└── test/                  # 16 test files (Vitest)
```

### State Management Architecture
| Concern | Technology | Files |
|---------|-----------|-------|
| Server state | TanStack Query | `src/hooks/queries.ts`, `src/lib/query-client.ts` |
| UI/workspace state | Zustand | `src/stores/workspace-store.ts` |
| Terminal state | Zustand | `src/stores/terminal-store.ts` |
| UI ephemeral state | Zustand | `src/stores/ui-store.ts` |
| Data cache | Zustand | `src/stores/data-store.ts` |
| User preferences | Zustand + Persist | `src/stores/preferences-store.ts` |
| Auth state | React Context | `src/components/auth/AuthProvider.tsx` |
| Theme state | React Context | `src/components/theme/ThemeProvider.tsx` |

### Widget System Architecture
```
Widget Registry (40+ definitions)
  ├── Categories: kpi, portfolio, risk, monitoring, ai, notification, chart, market
  ├── Search: by name, description, category
  ├── Filter: by category
  └── Metadata: defaultWidth, defaultHeight, component name

Dashboard Builder
  ├── Modal UI with search bar + category tabs
  ├── Grid of available widgets with metadata
  └── Adds selected widget as panel via WorkspaceStore

Dashboard Analytics
  ├── Compact: summary stats (counts, active panels)
  └── Full: category distribution with stacked bar chart

Widget Components (38)
  ├── Each imports its data via TanStack Query
  ├── All follow consistent Card + CardContent pattern
  └── All handle loading (Skeleton) and empty states
```

### TradingView Integration Suite
```
TVThemeSync          → Syncs app theme/chart options to lightweight-charts
TVCursorSync         → Synchronizes crosshair across multiple charts
TVIndicatorPalette   → 9 indicators across 4 categories (Trend, Momentum, Volatility, Volume)
TVTimeframeSelector  → 8 timeframes from 1m to 1w
TVComparisonMode     → Multi-symbol overlay with color management
TVChartLayoutSave    → Save/load/delete named chart layouts (localStorage)
```

### Provider Chain
```
<ThemeProvider>           ← dark mode, density, contrast, reduced motion
  <AuthProvider>          ← token management, login/logout
    <BrowserRouter>
      <QueryClientProvider>  ← TanStack Query cache
        <Routes>
          <Route path="/login" />
          <Route element={<AuthGuard />}>   ← protected routes
            <Route element={<Layout />}>    ← sidebar + topbar + outlet
              ...
            </Route>
          </Route>
        </Routes>
      </QueryClientProvider>
    </BrowserRouter>
  </AuthProvider>
</ThemeProvider>
```

### Performance Architecture
- **Code splitting**: `lazyLoad()` wrapper → Suspense → skeleton fallback
- **Component memoization**: `MemoizedWidget` wraps widgets in React.memo
- **Query caching**: TanStack Query with 10s staleTime, 2 retries
- **Animation**: Framer Motion spring physics (CSS animation where possible)
- **Bundle**: Vite build produces 530KB JS + 55KB CSS in 336ms

### Accessibility Architecture
- `useFocusTrap`: Modal/command-palette focus confinement
- `useKeyboardShortcut`: ⌘K palette, configurable hotkeys
- `announceToScreenReader`: Dynamic aria-live region
- CSS: `.sr-only` utility class for screen-reader-only content
- Focus: `:focus-visible` styling on all interactive elements

### WebSocket Architecture
```
useWebSocket(url, opts)
  ├── Auto-connect on mount
  ├── Exponential backoff reconnection (configurable: 3s wait, 10 max retries)
  ├── Status tracking (CONNECTED | DISCONNECTED | RECONNECTING)
  ├── send() for outbound messages
  └── reconnect() for manual reconnection

Channels (from websocket/client.ts):
  - trades, analytics, portfolio, notifications, preferences
```

## Backend Architecture
```
app.py → FastAPI app with CORS, auth middleware
├── api/           → 30+ route modules
├── market_data/   → Indicators, MTF, regime detection
├── exchange/      → Binance, Hyperliquid connectors
├── execution/     → Order management, position sizing
├── risk/          → Risk engine, scoring
├── intelligence/  → Whale, funding, OI, liquidity analyzers
├── pipeline/      → Signal generation, shadow engine
├── memory/        → Trade memory, pattern recognition
├── models/        → ML models for predictions
├── core/          → Shared utilities, database
└── tests/         → 785 pytest functions
```

## Key Metrics
| Metric | Value |
|--------|-------|
| Frontend source lines | ~12,000 |
| Backend test functions | 785 |
| Frontend test functions | 35 |
| UI Components | 25 |
| Dashboard Widgets | 38 |
| API Endpoint Files | 21 |
| Zustand Stores | 5 |
| Page Routes | 28 |
| NPM Packages | 14 |
| Python Dependencies | 13 |
