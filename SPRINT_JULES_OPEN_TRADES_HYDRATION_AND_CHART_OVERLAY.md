STANDING RULES (apply to this entire task):

1. Never trust this repo's own markdown docs (KNOWN_LIMITATIONS.md, TECHNICAL_DEBT.md,
   any *_REPORT.md/*_READINESS.md, etc.) as ground truth. Verify every claim against
   the actual current code before acting on it.

2. Never modify a test's assertion to match broken/wrong code just to turn it green.

3. Cut your branch off the current tip of `main`: `git fetch origin && git checkout -b
   <your-branch> origin/main`. Verify with `git log origin/main..HEAD --oneline` right
   before you push — it must show ONLY your own new commits. Open a Pull Request
   against `main`. Never push directly to `main`.

4. Before claiming any test count/status, actually run the FULL suite yourself —
   `pytest tests/ -q` — not just a subset, and paste the real final line in your
   summary. Also run the frontend checks: `npm run build` and `npm run test` (or
   whatever the real script names are — check `frontend/package.json`) and paste their
   real final output too.

5. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Task: hydrate open/closed trades on page load, then overlay entry/stop/target lines on the price chart

This is two related pieces in one PR: part A is a real correctness bug (open trades are
invisible after a page reload), part B is a UI feature that depends on part A actually
being correct to be trustworthy. Do them in that order.

## Part A — Background: verify this yourself, don't take this description as ground truth

Read `frontend/src/App.tsx`'s `AppRoutes()` function in full. Confirm:

- `openTrades`/`closedTrades` are `useState<TradePayload[]>([])` — both start empty.
- The *only* place either is ever set is inside `handleMessage()`, on `TRADE_OPENED` /
  `TRADE_CLOSED` websocket events (`setOpenTrades((prev) => [...prev, p])` etc.).
- There is no REST fetch anywhere in this file (or a parent that hydrates it) that loads
  the trades that were already open *before* this page load / reload / new tab. Confirm
  this by searching the whole file for `apiFetch` and checking what each call actually
  populates.

This means: on every fresh page load or hard refresh, `openTrades` is empty and stays
empty until a *new* trade event happens to arrive over the websocket during that session.
Any trade that was already open before the page loaded is invisible. Confirm the real
user-facing impact by checking who consumes `openTrades`/`closedTrades` via
`useOutletContext<LayoutContext>()` — at minimum `frontend/src/pages/Overview.tsx` (the
"Trades" card's count), `frontend/src/pages/Portfolio.tsx` (`positions =
openTrades.map(...)`), `frontend/src/pages/Trades.tsx`, and
`frontend/src/pages/DecisionCenter.tsx` (uses `openTrades.some(t => t.symbol ===
signal.symbol)` to decide whether a signal already has an open position) — search for all
real consumers yourself, this list may not be exhaustive.

## Part A — What to build

1. Find the right existing backend endpoint to hydrate from — do not invent a new one if
   an existing one already fits. Compare, yourself, the response shapes and query
   semantics of `GET /paper/trades` (`api/routes/paper.py`, returns `entry`/`stop`/`tp1`
   per trade already, check if it filters by open status or needs a query param) and `GET
   /terminal/open-trades` (`api/routes/terminal.py` → `TerminalService.get_open_trades()`
   in `services/terminal_service.py`, currently returns `entry_price`/`id` instead of
   `entry`/`trade_id`, and does not currently include `stop`/`tp1`/`tp2` at all). Pick
   whichever is the better fit for "give me all currently-open trades for this user" and
   say why in your PR. If you pick `/terminal/open-trades`, you'll need to add
   `stop`/`tp1`/`tp2` to `TerminalService._get_open_trades()`'s returned dict (trivial —
   they're already real columns on `database.py`'s `Trade` model, same as `entry`).
2. In `frontend/src/App.tsx`, add a fetch (on mount / when `token` becomes available,
   alongside the existing websocket-connect `useEffect`) that loads currently-open trades
   via the endpoint you picked, maps the response into `TradePayload[]` shape
   (`frontend/src/types/trade.ts`), and seeds `openTrades` with it *before* or
   concurrently with the websocket connecting — the websocket's own
   `TRADE_OPENED`/`TRADE_CLOSED` events must keep working exactly as they do today on top
   of this initial hydration (a trade opened live during the session must still appear
   immediately; the fix here is only about what's already open at load time).
3. Decide whether `closedTrades` also needs an initial hydration (check what actually
   consumes it and whether an empty list on load is a real problem there too, e.g. recent
   PnL history) or whether it's acceptable to stay session-only — state your reasoning in
   the PR either way, don't silently skip it without checking.
4. Handle the trivial races correctly: if the initial REST fetch and a live
   `TRADE_OPENED` websocket event for the same trade both land, the trade must not appear
   twice in `openTrades` (dedupe by `trade_id`/`id`).

## Part B — Background: verify this yourself

Read `frontend/src/components/trading/chart-panel.tsx` in full. It already draws
overlays on the `lightweight-charts` price chart for the current symbol: support/resistance
levels via `candleSeries.createPriceLine({ price, color, lineWidth, lineStyle, title, ...
})`, plus RSI divergence and trend-channel lines via separate `LineSeries`. This is the
exact pattern to follow — do not invent a different overlay mechanism.

`database.py`'s `Trade` model already has real `entry`, `stop`, `tp1`, `tp2` columns for
every trade, populated at trade-open time (see `execution/tp_sl.py` for how they're
computed). Once Part A is done, `openTrades` (available via `LayoutContext`, see
`frontend/src/components/layout/Layout.tsx`) reliably reflects every currently-open trade,
including its `entry`/`stop`/`tp1`/`tp2` if you extended the payload in Part A step 1.

`frontend/src/pages/TradingWorkspace.tsx` (the page that renders `<ChartPanel
data={candles} />`) is already a child route of `<Layout>` (see
`frontend/src/App.tsx`'s route tree) but currently does **not** call
`useOutletContext<LayoutContext>()` at all — it will need to start doing so to reach
`openTrades`.

## Part B — What to build

1. In `TradingWorkspace.tsx`, pull `openTrades` from `useOutletContext<LayoutContext>()`
   and filter to the trade(s) open for the currently-displayed symbol (the page already
   tracks/derives the current symbol somewhere — verify how, e.g.
   `useTerminalStore()`, same store `chart-panel.tsx` already reads `symbol` from).
   Pass the matching open trade(s) down to `ChartPanel` as a new prop.
2. In `chart-panel.tsx`, for each open trade passed in, draw price lines for `entry`,
   `stop`, `tp1`, and `tp2` (skip any that are null/zero) using
   `candleSeries.createPriceLine(...)`, following the exact same call shape already used
   for S/R levels just above in the same file. Give each a distinct, clear color/style so
   they're visually distinguishable from the existing S/R/divergence/channel overlays and
   from each other (e.g. entry neutral, stop red, targets green — pick something coherent
   with this file's existing green=bullish/red=bearish convention, don't invent a new
   palette) and a `title` label like `"ENTRY"` / `"STOP"` / `"TP1"` / `"TP2"`.
3. If a symbol has more than one open trade (confirm whether that's actually possible in
   this app — check risk/position-limit logic — and handle it sensibly either way: either
   draw lines for all of them, or state in your PR why only showing one is correct).
4. Clean up these price lines correctly when the symbol changes or the component unmounts
   (the existing S/R-level code in this same file already has to deal with this via the
   `useEffect` cleanup — follow the same pattern, don't leak stale price lines onto a
   newly-loaded chart for a different symbol).

## Explicitly out of scope

- Do not touch the scanner (`scanner/core.py`, `Opportunity` model) — `Opportunity` has no
  entry/stop/target fields today and this task is not about adding them; it's about
  showing *actual open trades'* real entry/stop/target on the chart, which already exist
  on `Trade`.
- Do not add new websocket event types — the fix in Part A is a one-time REST hydration
  on load, the existing `TRADE_OPENED`/`TRADE_CLOSED` events remain the live-update path.
- Do not modify `execution/tp_sl.py`'s stop/target calculation logic — only surface the
  values it already computes and already stores on `Trade`.
- Do not touch `frontend/src/components/charts/*` (WinRateChart, PerformanceChart,
  DrawdownChart) or `frontend/src/components/portfolio/ExposureChart.tsx` — unrelated,
  different charts serving different pages.
- Do not add a symbol-search or trade-picker UI — the overlay is automatic based on
  whatever symbol is currently displayed.

## Test plan expectations

- Backend (if you extended `TerminalService._get_open_trades()` or any route response):
  a unit/integration test asserting the endpoint's response now includes `stop`/`tp1`/`tp2`
  for an open trade fixture, matching the real column values.
- Frontend: a test for the new hydration effect in `App.tsx` (or wherever you place it) —
  mock the fetch, assert `openTrades` is populated before/independent of any websocket
  message, and assert no duplicate entry appears if a `TRADE_OPENED` event for the same
  `trade_id` arrives after hydration.
- Frontend: a test for `chart-panel.tsx` (there's already
  `frontend/src/test/components/ChartPanel.test.tsx` — extend it, check its existing
  conventions for mocking `lightweight-charts` first) asserting `createPriceLine` is
  called with the right price/title for a passed-in open trade, and that it is *not*
  called for a trade with a null/zero stop or target.
- Run the full backend suite (`pytest tests/ -q`) and the frontend `npm run build` /
  `npm run test`, and paste the real final output of each in your summary.
