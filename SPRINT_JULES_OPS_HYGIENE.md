# Sprint: Ops Hygiene (CI coverage + doc accuracy)

## Context

This is independent of the other active sprints (test-suite stabilization, crystal brain hero) — it doesn't touch any file those touch, safe to run in parallel.

**This repo's own docs are currently unreliable** — that's exactly what part 2 of this sprint fixes. `KNOWN_LIMITATIONS.md`, `TECHNICAL_DEBT.md`, and `MASTER_BOOK.md` were checked against the actual code and several "critical bug" claims in them turned out to be false or already fixed (an ATR column typo claim, a missing `pandas_ta` dependency claim, and a ConfidenceEngine "double-scaling" claim were all disproven by reading the real code). Don't repeat that mistake in reverse — every claim you write in this sprint must be something you personally verified against current code/tests, not copied from an existing doc or assumed.

## Part 1 — CI: add frontend test coverage

`.github/workflows/ci.yml` currently has a `frontend` job that only runs `npm run build` — it never runs the test suite (`frontend/vitest.config.ts` exists, and there are test files under `frontend/src/test/`), so frontend regressions aren't caught by CI at all.

1. Add a test step to the `frontend` job in `.github/workflows/ci.yml`, before or after the build step (check `frontend/package.json` scripts for the correct npm script name — likely `npm run test` or `npx vitest run`; use whatever is actually wired up, don't invent a script that doesn't exist).
2. Confirm it actually runs and passes locally before considering this done (`cd frontend && npm run <test-script>`).
3. If the current frontend test suite has real failures (not flakiness), report them clearly in your summary — do not silently skip or delete failing tests to make CI green.

## Part 2 — Rewrite KNOWN_LIMITATIONS.md and TECHNICAL_DEBT.md to match reality

1. Read the current `KNOWN_LIMITATIONS.md` and `TECHNICAL_DEBT.md` in full.
2. For every claim in both files, verify it against the actual current code (grep for the referenced file/line, read it, and if it's a "bug" claim, write or run a quick check that actually demonstrates the behavior — don't take the doc's word for it).
3. Remove/correct any claim that's false or already fixed. Keep and rephrase-if-needed any claim you've confirmed is still real.
4. Add any *new* real limitation you notice while doing this pass (e.g., anything still open from the other active sprints, or anything you find independently) — but only things you've personally verified, with a file/line reference.
5. Add one line at the top of each file noting the date of this verification pass, so future readers know how fresh it is (e.g. "Last verified against code: <date>, not just written from memory/assumption").
6. Do the same sanity pass on the "952 tests passing" / readiness claims in `docs/PROJECT_MEMORY/MASTER_BOOK.md` and `PROJECT_STATUS.md` if you have time — run the actual test suite (`pytest tests/ -q`) and correct the numbers if they're stale, but this is lower priority than items 1-5 above; don't let it block finishing the core doc rewrite.

## Explicit non-goals

- Don't touch any backend logic, don't touch frontend components beyond the CI config file — this sprint is CI config + documentation only.
- Don't merge/rewrite `BACKLOG.md`, `DECISIONS.md`, or `RELEASE_HISTORY.md` — out of scope.

## Acceptance criteria

- CI's `frontend` job runs and passes an actual test step, not just a build.
- `KNOWN_LIMITATIONS.md` and `TECHNICAL_DEBT.md` contain only claims you personally verified against current code, each with a concrete file/line reference where applicable, and a "last verified" date at the top.
- Your summary explicitly lists which old claims you removed/corrected and why (what you found when you checked).
