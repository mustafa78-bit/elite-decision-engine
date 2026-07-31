STANDING RULES (apply to this entire sprint):

1. Never trust this repo's own markdown docs (KNOWN_LIMITATIONS.md, TECHNICAL_DEBT.md,
   MASTER_BOOK.md, PROJECT_STATUS.md, etc.) as ground truth. They have repeatedly been
   found stale or simply wrong. Verify every claim — including claims in THIS sprint
   doc — against the actual current code and by running the actual test with a full
   traceback (`pytest path::test --tb=long`) before acting on it.

2. When a test fails, first determine WHICH is wrong: the test's expectation, or the
   code's behavior. Do not default to changing whichever is easier to change. If you
   change a shared constant, enum, threshold, or weight to make a test pass, you must
   first grep for every other place that value is used/imported and confirm your
   change doesn't alter behavior there. State in your summary that you did this check
   and what you found.

3. Never modify a test's assertion to match broken/wrong code just to turn it green.
   If you believe the test itself is outdated or asserting the wrong thing, say so
   explicitly in your summary with your reasoning.

4. You must work on your own branch and open a Pull Request against `main`. Never
   push directly to `main`. Do not report a task as "done" until there is a real PR
   with a real diff — a chat summary of what you did is not sufficient.

5. Before claiming "all tests pass" or "N failures fixed", actually run the test
   suite yourself and paste the real final line in your summary. A prior report on
   a different sprint in this repo claimed "1,325+ passing, zero failures" when the
   real number was 29 still failing — don't repeat that.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint: Integrate NexusDashboard hero into CommandDeck with real data

## Context

A new component `frontend/src/components/hq/NexusDashboard.tsx` was just added to this
branch — it's a Gemini-generated (then hand-edited) full visual layout matching the
final approved NEXUS design: top header (SYSTEM STATUS / NEXUS title / LIVE SYNC+clock),
left/right sidebar stat cards, a center animated brain hero with holographic ripples and
traveling neural light-pulses along its neural pathways, a "Perceiving·Reasoning·
Learning·Deciding·Evolving" status tracker, and a bottom "NEXUS SPEAKS / AI REASONING
CONSOLE" panel with a waveform visualization. `lucide-react` has already been added as a
dependency for its icons — confirm it's in `frontend/package.json` before starting.

**Right now every value in `NexusDashboard.tsx` is hardcoded/placeholder** (e.g.
`REGIME: HIGH-GROWTH (92%)`, `DECISIONS: 48 (ALL OPTIMAL)`) and the component is not
wired into any route yet. Your job is to make it real and make it live where
`CommandDeck.tsx` currently lives.

**Also important — don't lose existing functionality.** A previous sprint already built
into `CommandDeck.tsx` / `OLLOCommander.tsx`: voice input (SpeechRecognition, en-US/tr-TR),
voice output (SpeechSynthesis), and conversational routing (OLLO responses carry an
`intent_route` field that triggers `useNavigate`). The AI Experience page (SignalFeed,
AnalysisDashboard) was also already merged into CommandDeck. None of that should be lost —
it needs to end up living inside/alongside the new NexusDashboard layout, not deleted.

## Your task

1. **Reconcile the two components.** Decide (and explain your reasoning in the summary)
   whether `NexusDashboard.tsx` replaces `CommandDeck.tsx`'s layout wholesale with the
   existing OLLO voice/chat/routing logic moved into its "NEXUS SPEAKS" panel, or whether
   `CommandDeck.tsx` renders `NexusDashboard` as its main layout and passes down the
   existing OLLO state/handlers as props. Either is fine — just don't end up with two
   competing hero UIs on the same route, and don't silently drop the voice/routing feature.

2. **Wire real data into every card**, replacing the hardcoded strings. Investigate and
   verify each endpoint's actual response shape before using it — don't guess field names:
   - `api/routes/dashboard.py`'s `GET /dashboard/hero` endpoint already aggregates market
     regime, confidence, risk, and portfolio snapshot data in one call (see
     `HeroBannerDTO`) — start here, it likely covers Market Regime, AI Confidence, Risk
     Level, and Portfolio Status directly or with minor adaptation.
   - BTC Trend → check `api/routes/market.py` / `api/routes/market_live.py`.
   - Whale Activity → check `api/routes/whale.py`.
   - Evidence Summary → check `api/routes/evidence.py`.
   - Live Decisions / Active Signals → check `api/routes/signals.py` and
     `api/routes/dashboard.py`'s other endpoints (`/dashboard/overview`, `/dashboard/kpi`).
   - System Health → check `api/routes/monitoring.py` (`/health`, `/dashboard/monitoring`).
   - If no clean existing endpoint covers a card, say so explicitly in your summary rather
     than inventing fake data or silently leaving it hardcoded.

3. **Feed the "NEXUS SPEAKS" console from the real OLLO conversation**, not the hardcoded
   "I am analyzing market structure..." text — it should show the actual latest OLLO
   response text (and ideally reuse the waveform as a visual accompaniment to the existing
   TTS voice output, not a fake decorative animation).

4. **Keep the brain's status tracker meaningful** — if there's a natural mapping from the
   app's real state to Perceiving/Reasoning/Learning/Deciding/Evolving (e.g. based on
   whether OLLO is actively fetching/thinking vs idle), wire it; otherwise leave it as a
   reasonable static/cyclical indicator and say so in your summary rather than faking
   real-time meaning it doesn't have.

5. Run `npm run build` and `npm run test` (frontend) — both must pass clean.

## Explicit non-goals

- Don't touch backend trading/decision logic — only read from existing endpoints.
- Don't redesign the visual layout — `NexusDashboard.tsx` as committed (including the
  neural light-pulse animation) is the approved look; adapt data into it, don't change
  its structure/aesthetic without a strong reason (explain if you do).

## Acceptance criteria

- `/command-deck` (and `/`) renders the new NexusDashboard hero with real backend data in
  every card, no hardcoded placeholder values remaining unless explicitly justified in
  your summary.
- Voice input/output and conversational intent-based routing still work exactly as before.
- `npm run build` and `npm run test` both pass clean, zero new TypeScript errors.
- List every endpoint you wired to every card in your summary, file/line references
  included.
