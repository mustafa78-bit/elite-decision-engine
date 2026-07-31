STANDING RULES (apply to this entire sprint):

1. Never trust this repo's own markdown docs (KNOWN_LIMITATIONS.md, TECHNICAL_DEBT.md,
   MASTER_BOOK.md, PROJECT_STATUS.md, etc.) as ground truth. They have repeatedly been
   found stale or simply wrong. Verify every claim — including claims in THIS sprint
   doc — against the actual current code before acting on it.

2. Never modify a test's assertion to match broken/wrong code just to turn it green.
   If you believe a test is outdated or asserting the wrong thing, say so explicitly
   in your summary with your reasoning.

3. You must work on your own branch and open a Pull Request against `main`. Never
   push directly to `main`. Do not report a task as "done" until there is a real PR
   with a real diff — a chat summary of what you did is not sufficient.

4. This sprint is intentionally scoped small on purpose — previous larger, multi-file
   sprints repeatedly failed to complete. If you get stuck on one card's data source,
   skip it, say so explicitly in your summary, and keep going on the rest — don't let
   one blocker stop the whole sprint from being pushed.

5. In your final summary, list the exact files you changed, one line per file
   describing the change and why, AND list which endpoint you wired to which card.

# Sprint B (of 2): Wire real data into NexusDashboard's cards

## Context

**Prerequisite: Sprint A ("Wire NexusDashboard into CommandDeck — structure only") must
already be merged before you start this one** — `NexusDashboard.tsx` should already be
rendering live at `/command-deck` with all its existing voice/routing functionality
intact, just with hardcoded placeholder values in its stat cards. If that's not the
state you find, stop and say so in your summary rather than guessing.

Your job now is only to replace the hardcoded placeholder strings with real data from
the backend. Do not touch layout, animation, voice, or routing logic — that's all done.

## Your task

Investigate and verify each endpoint's actual response shape before using it (read the
route file, don't guess field names):

- `api/routes/dashboard.py`'s `GET /dashboard/hero` endpoint already aggregates market
  regime, confidence, risk, and portfolio snapshot data in one call (see `HeroBannerDTO`
  in that file) — start here, it likely covers **Market Regime**, **AI Confidence**,
  **Risk Level**, and **Portfolio Status** directly or with minor adaptation.
- **BTC Trend** → check `api/routes/market.py` / `api/routes/market_live.py`.
- **Whale Activity** → check `api/routes/whale.py`.
- **Evidence Summary** → check `api/routes/evidence.py`.
- **Live Decisions** / **Active Signals** → check `api/routes/signals.py` and
  `api/routes/dashboard.py`'s other endpoints (`/dashboard/overview`, `/dashboard/kpi`).
- **System Health** → check `api/routes/monitoring.py` (`/health`,
  `/dashboard/monitoring`).
- If no clean existing endpoint covers a card, say so explicitly in your summary rather
  than inventing fake data or silently leaving it hardcoded — skip that one card and
  move on to the rest.

Additionally:

- **"NEXUS SPEAKS" console**: replace the hardcoded "I am analyzing market structure..."
  text with the actual latest OLLO response text (it should already be available in
  whatever state/props Sprint A wired up for voice output — reuse that, don't
  re-fetch separately).
- **Status tracker** (Perceiving·Reasoning·Learning·Deciding·Evolving): if there's a
  natural real-state mapping (e.g. OLLO actively fetching vs idle), wire it; otherwise
  leave it as a reasonable static/cyclical indicator and say so explicitly rather than
  faking real-time meaning it doesn't have.

## Explicit non-goals

- Don't touch backend trading/decision logic — only read from existing endpoints.
- Don't change the visual layout, animation, or structure done in Sprint A.
- Don't touch voice input/output or routing logic — already working, leave it alone.

## Acceptance criteria

- Every card shows real data from a real endpoint, OR is explicitly listed in your
  summary as skipped with a reason.
- "NEXUS SPEAKS" shows real OLLO conversation text, not a hardcoded string.
- `npm run build` and `npm run test` both pass clean, zero new TypeScript errors.
- Voice input/output and intent-based routing from Sprint A still work unchanged.
- Your summary lists every endpoint wired to every card, with file/line references.
