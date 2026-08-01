# OFFLINE Root Cause Report

## Symptoms

1. **Header badge shows "Offline"** — `ConnectionStatusBadge` always renders `"Offline"` regardless of backend state.
2. **Widgets fail to load** — All widget API calls (`apiFetch`) fail silently; components show empty states.
3. **Browser console: `ERR_CONNECTION_REFUSED`** — TCP connection to `http://localhost:8000` is refused.

## Found Root Causes

### Root Cause 1: ConnectionStatusBadge logic checks rooms that never connect

| File | Line | Issue |
|---|---|---|
| `frontend/src/types/connection.ts` | 3-8 | `WsRoomStatus` declares 5 rooms: `trades`, `analytics`, `portfolio`, `notifications`, `preferences` |
| `frontend/src/App.tsx` (`AppShell`) | ~73-79 | `useState<WsRoomStatus>` initializes all 5 rooms to `"DISCONNECTED"` |
| `frontend/src/App.tsx` (`AppShell`) | ~145 | Only `trades` status is ever updated: `setWsRooms((prev) => ({ ...prev, trades: s }))` |
| `frontend/src/components/layout/ConnectionStatus.tsx` | 20 | `Object.values(wsRooms).every((s) => s === "CONNECTED")` |

**The bug:**
`ConnectionStatusBadge` checks ALL 5 rooms. But only `trades` is ever wired up in `AppShell`. The other 4 rooms (`analytics`, `portfolio`, `notifications`, `preferences`) remain `"DISCONNECTED"` for the lifetime of the app. Therefore `allOk` is ALWAYS `false`, and the badge ALWAYS renders `"Offline"` — even if the backend is perfectly healthy and the trades socket is connected.

**Code path (full trace):**

```
AppShell (App.tsx)
  ↳ useState<WsRoomStatus>({ trades: "DISCONNECTED", analytics: "DISCONNECTED", ... })
  ↳ useEffect → connectTradesSocket(handler, (s) => setWsRooms(prev => ({...prev, trades: s})))
                                  ↳ ONLY trades is updated
  ↳ renders <Layout status wsRooms={wsRooms} />
      ↳ renders <Header wsRooms={wsRooms} />
          ↳ renders <ConnectionStatusBadge wsRooms={wsRooms as unknown as Record<string, CS>} />
              ↳ Object.values(wsRooms).every(s => s === "CONNECTED")
              ↳ 5 values → 4 are "DISCONNECTED" → allOk = FALSE
              ↳ renders "Offline" ← ALWAYS
```

### Root Cause 2: ERR_CONNECTION_REFUSED — backend not reachable

All HTTP and WebSocket requests use `http://localhost:8000` derived from:

```
frontend/.env: VITE_API_URL=http://localhost:8000
frontend/src/api/client.ts: BASE_URL = import.meta.env.VITE_API_URL
```

`ERR_CONNECTION_REFUSED` is a browser-level TCP error. It means nothing is listening on `localhost:8000`. This is not a frontend code defect — it is an operational state (the backend process `uvicorn` is not running or is on a different port).

**All API call sites use the same derived URL:**

| Component | File | Call | URL |
|---|---|---|---|
| `Dashboard` | `pages/Dashboard.tsx:23` | `useApi(() => fetchKpiDetail())` | `http://localhost:8000/widgets/kpi/detail` |
| `MonitoringStatus` | `components/dashboard/MonitoringStatus.tsx:14` | `fetchMonitoringWidgetStatus()` | `http://localhost:8000/widgets/monitoring/status` |
| `PortfolioSummaryCard` | `components/dashboard/PortfolioSummaryCard.tsx:13` | `fetchPortfolioWidgetSummary()` | `http://localhost:8000/widgets/portfolio/summary` |
| `NotificationPanel` | `components/dashboard/NotificationPanel.tsx:15` | `fetchNotificationsWidget(5)` | `http://localhost:8000/widgets/notifications?limit=5` |
| `FounderHealthWidget` | `components/dashboard/founder-health-widget.tsx:34-41` | `apiFetch("/health")` etc. | `http://localhost:8000/health` |
| `HeroDashboard` | `pages/HeroDashboard.tsx:74-77` | `apiFetch("/intelligence")` etc. | `http://localhost:8000/intelligence` |
| `MonitoringWidget` | `components/dashboard/monitoring-widget.tsx:19` | `fetchMonitoringWidgetStatus()` | `http://localhost:8000/widgets/monitoring/status` |
| WebSocket (trades) | `websocket/client.ts:24` | `new WebSocket(url)` | `ws://localhost:8000/ws/trades?token=...` |

**No URL mismatch exists.** All paths use the single `VITE_API_URL` source. If one fails, all fail.

### Root Cause 3: Silent error handling hides failures

Multiple widget components swallow errors silently:

| File | Line | Code |
|---|---|---|
| `MonitoringStatus.tsx` | 16-18 | `catch { // silent }` |
| `PortfolioSummaryCard.tsx` | 15-17 | `catch { // silent }` |
| `NotificationPanel.tsx` | 18-20 | `catch { // silent }` |
| `FounderHealthWidget.tsx` | 34, 90 | `catch(() => null)` then `.catch(() => { /* set all OFFLINE */ })` |
| `useApi.ts` | 27-34 | Sets `error` string but Dashboard only shows "Failed to load KPIs" |

When the backend is unreachable, these components silently fall into their empty/loading states with no indication to the user that the backend connection failed. The only visible symptom is the Header's "Offline" badge (Root Cause 1) and empty widget cards.

## Verification

Confirmed by reading all components listed above. No hardcoded URLs exist anywhere in `frontend/src/`. All HTTP traffic uses `apiFetch` with `BASE_URL` derived from `VITE_API_URL`. All WebSocket traffic uses `getWsBaseUrl()` derived from `VITE_API_URL`.

## Correct Fixes

### Fix 1: ConnectionStatusBadge — only check connected rooms

**Problem:** `ConnectionStatusBadge` checks all 5 rooms but only `trades` is ever updated.

**Fix:** In `ConnectionStatus.tsx`, change the check to only consider rooms that have been connected at least once, or remove unused rooms from the status object entirely.

**Minimal fix** — `frontend/src/components/layout/ConnectionStatus.tsx` line 20:
```typescript
// Before:
const allOk = Object.values(wsRooms).every((s) => s === "CONNECTED");

// After: only check rooms that have ever been connected
const connectedCount = Object.values(wsRooms).filter((s) => s === "CONNECTED").length;
const allOk = connectedCount > 0;
```

Or more precisely, reduce `WsRoomStatus` to only the `trades` room, and expand it when other rooms are connected.

### Fix 2: ERR_CONNECTION_REFUSED — not a code fix

No frontend code change can fix `ERR_CONNECTION_REFUSED`. The backend must be running:

```bash
python -m uvicorn api.main:app --port 8000
```

Run this in a separate terminal before launching the frontend.

### Fix 3: Log fetch errors for debuggability

At minimum, log errors to console in widget catch blocks:

```typescript
catch (err) {
  console.error("MonitoringStatus: failed to load", err);
}
```
