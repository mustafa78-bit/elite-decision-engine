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
   sprints repeatedly failed to complete. Stay inside the scope below. If you get
   stuck on one part, push what you have completed and clearly say what's blocked
   rather than reporting total failure with nothing pushed.

5. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint A (of 2): Wire NexusDashboard into CommandDeck — structure only, no data yet

## Context

`frontend/src/components/hq/NexusDashboard.tsx` exists on this branch — a full visual
layout (header, sidebar stat cards, animated brain hero with neural light-pulses, bottom
"NEXUS SPEAKS" console) matching the approved NEXUS design. `lucide-react` is already a
dependency. **All card values in it are currently hardcoded placeholders — that's fine
for this sprint, a second sprint will wire real data in afterward. Do not attempt to wire
real data in this sprint — that's explicitly out of scope here, to keep this small.**

`CommandDeck.tsx` currently renders the *old* smaller hero (`OLLOCommander.tsx`) plus
already has, from earlier work: voice input (SpeechRecognition, en-US/tr-TR), voice
output (SpeechSynthesis), conversational routing (OLLO responses carry `intent_route`,
triggers `useNavigate`), and the merged AI Experience content (SignalFeed,
AnalysisDashboard — `/ai-experience` route was already removed).

## Your one job this sprint

Make `NexusDashboard.tsx` the thing that actually renders at `/command-deck` (and `/`),
**without losing any existing functionality.**

1. Decide and implement one of:
   - (a) `NexusDashboard` becomes the new structure of `CommandDeck.tsx` — move the
     existing OLLO voice/chat/routing logic and state into `NexusDashboard`'s "NEXUS
     SPEAKS" panel area, or
   - (b) `CommandDeck.tsx` keeps its existing logic/state and renders `NexusDashboard`
     as its visual layout, passing the OLLO state/handlers down as props.
   Either is fine. State which one you picked and why in your summary.

2. Preserve, working exactly as before:
   - Voice input button/flow (mic → SpeechRecognition → query)
   - Voice output (SpeechSynthesis reads OLLO's response)
   - `intent_route`-based navigation (asking about "portfolio" navigates to `/portfolio`, etc.)
   - Whatever AI Experience content (signal feed / analysis dashboard) was already merged in

3. It's fine if `NexusDashboard`'s stat cards still show hardcoded placeholder text after
   this sprint — just make sure the whole page renders without crashing and nothing
   existing regresses.

4. Run `npm run build` and `npm run test` (both in `frontend/`) — both must pass clean,
   zero new TypeScript errors.

## Explicit non-goals (do NOT do these — they're Sprint B)

- Do not wire any card to real backend data.
- Do not change the "NEXUS SPEAKS" console text source yet (hardcoded placeholder text
  there is fine for now, as long as it doesn't visually break when real OLLO responses
  come in later — i.e. don't hardcode a fixed-height container that would clip longer
  real text, but don't go fetch real text either).
- Do not touch backend code at all.
- Do not change the visual design of `NexusDashboard.tsx` itself.

## Acceptance criteria

- `/command-deck` and `/` render `NexusDashboard`'s layout.
- Voice input/output and intent-based routing still work exactly as before this sprint.
- Previously-merged AI Experience content is still present somewhere in the page.
- `npm run build` and `npm run test` both pass clean.
- A real PR exists with a real diff.
