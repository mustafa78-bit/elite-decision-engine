# API Integration — Elite Terminal

## Base Configuration

- **Base URL:** `http://localhost:8000`
- **Client:** `api/client.ts` — `apiFetch<T>()` generic fetch wrapper
- **Auth:** JWT token (via AuthProvider/AuthGuard)
- **Cache:** TanStack React Query (10s stale time, 2 retries)
- **Real-time:** WebSocket at ws://localhost:8000/ws

## API Modules

| Module | File | Endpoints Consumed |
|--------|------|--------------------|
| KPI Widgets | `api/widgets.ts` | `GET /widgets/kpi/detail`, `GET /widgets/portfolio/summary`, `GET /widgets/monitoring/status`, `GET /widgets/notifications` |
| Portfolio | `api/portfolio.ts`, `api/portfolio_detail.ts` | `GET /portfolio`, `GET /portfolio/summary`, `GET /portfolio/distribution`, `GET /portfolio/performance`, `GET /portfolio/risk` |
| Scanner | `api/signals.ts` | `GET /signals?limit=N` |
| Scanner Categories | (via `api/client.ts`) | `GET /scanner/category/{category}?n=N`, `GET /scanner/categories` |
| Watchlists | `api/watchlists.ts` | CRUD: `GET /watchlists`, `POST /watchlists`, `PUT /watchlists/{id}`, `DELETE /watchlists/{id}`, `POST /watchlists/{id}/symbols`, `DELETE /watchlists/{id}/symbols/{symbol}` |
| Timeline | `api/timeline.ts` | `GET /timeline/signals`, `GET /timeline/trades`, `GET /timeline/global` |
| Notifications | `api/notifications.ts`, `api/notifications_detail.ts` | `GET /notifications`, `GET /notifications/stats`, `POST /notifications/{id}/read`, `POST /notifications/read-all`, `DELETE /notifications/{id}`, `DELETE /notifications/read` |
| Preferences | `api/preferences.ts` | `GET /preferences/{user_id}`, `PUT /preferences/{user_id}`, `PUT /preferences/{user_id}/theme`, `PUT /preferences/{user_id}/layout` |
| Intelligence | `api/intelligence.ts` | Intelligence data |
| Execution | `api/execution.ts` | Trade execution endpoints |
| Risk | `api/risk.ts` | Risk metrics |
| Regime | `api/regime.ts` | `GET /regime` |
| Paper Trading | `api/paper.ts` | Paper trading operations |
| Performance | `api/performance.ts` | Performance metrics |
| Backtest | `api/backtest.ts` | Backtest operations |
| Journal | `api/journal.ts` | Trade journal entries |
| Trading Control | `api/trading_control.ts` | Trading controls |
| Signals Ranking | `api/signals_ranking.ts` | `GET /signals/ranking` |

## WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `TRADE_OPENED` | Server→Client | `TradePayload` |
| `TRADE_CLOSED` | Server→Client | `TradePayload` |
| `MARKET_UPDATE` | Server→Client | `MarketPayload` |
| `SIGNAL_UPDATE` | Server→Client | `SignalPayload` |
| `RISK_UPDATE` | Server→Client | `RiskWsPayload` |
| `PRICE_UPDATE` | Server→Client | `PriceWsPayload` |
| `CANDLE_UPDATE` | Server→Client | `CandleWsPayload` |
| `VOLUME_UPDATE` | Server→Client | `VolumeWsPayload` |

## Data Flow Pattern

```
Pages → useQuery / apiFetch → Backend REST API
                                   ↕
App.tsx ← WebSocket ← Backend WS Server
  ↓
Layout (Outlet context)
  ↓
Child pages (useOutletContext<LayoutContext>())
```

## Hooks

| Hook | Purpose |
|------|---------|
| `useWebSocket(url, opts)` | WebSocket with auto-reconnect |
| `useApi(fn, deps)` | Fetch-on-mount pattern |
| `useLiveUpdates()` | React Query with polling |
| `useKpis()` | KPI widget data (10s refresh) |
| `usePortfolioSummary()` | Portfolio summary (10s refresh) |
| `useRegime()` | Market regime (30s refresh) |
| `useMonitoring()` | System monitoring (15s refresh) |
| `useNotifications(limit)` | Recent notifications (15s refresh) |
| `useWatchlists()` | Watchlist data (30s refresh) |
| `useSignals()` | Signal data (20s refresh) |
| `usePortfolio()` | Portfolio data (10s refresh) |
