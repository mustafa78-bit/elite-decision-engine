STANDING RULES (apply to this entire sprint):

1. Never trust this repo's own markdown docs (KNOWN_LIMITATIONS.md, TECHNICAL_DEBT.md,
   MASTER_BOOK.md, PROJECT_STATUS.md, etc.) as ground truth. Verify every claim against
   the actual current code before acting on it.

2. Never modify a test's assertion to match broken/wrong code just to turn it green.
   If you believe a test is outdated or asserting the wrong thing, say so explicitly
   in your summary with your reasoning.

3. You must work on your own branch and open a Pull Request against `main`. Never
   push directly to `main`. Do not report a task as "done" until there is a real PR
   with a real diff — a chat summary of what you did is not sufficient for review.

4. This sprint is intentionally scoped small on purpose. If you get stuck, push what
   you have and say what's blocked.

5. Before claiming any test count/status, actually run `pytest tests/ -q` yourself,
   and this time also note the **wall-clock duration** pytest reports at the end
   (e.g. "1350 passed ... in 833.94s") — that number is the actual point of this
   sprint, not just the pass/fail count.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint: Fix test suite slowdown from the dynamic coin universe change

## Context

A prior sprint made `OpportunityScanner()` (no explicit `symbols=` argument) default
to a live, network-backed dynamic coin universe (`market_data/universe.py`,
`get_top_volume_symbols()`) instead of an instant hardcoded 3-symbol list. That's the
correct behavior for the *running app*, but three places in the real (non-test) codebase
construct `OpportunityScanner()` this way:

- `api/routes/scanner.py:13` — `_scanner = OpportunityScanner()` (module-level lazy
  singleton backing `/scanner/top-opportunities`, `/scanner/dashboard`,
  `/scanner/category/{category}`)
- `decision/aggregator.py:32` — `self.scanner = scanner or OpportunityScanner()`
- `services/terminal_service.py:30` — `self.scanner = scanner or OpportunityScanner()`

Any test that exercises these code paths without mocking `get_top_volume_symbols` (or
passing an explicit scanner/symbols) now makes a real, unmocked HTTP call to Binance,
with the provider's own timeout (10s) on every uncached attempt. This is very likely why
the full suite's runtime jumped from ~150-170s to **833s** after that sprint merged, even
though it currently causes 0 test failures (a related singleton-isolation bug that *did*
cause 2 failures was already fixed separately — this sprint is only about the slowdown
that remains after that fix).

## Your task

1. Find every test that exercises `api/routes/scanner.py`'s routes, `decision/aggregator.py`,
   and `services/terminal_service.py` (search for how each is imported/used in `tests/`).
2. For each one that doesn't already mock the scanner/universe, add a mock so it never
   makes a real network call — the standard pattern already used elsewhere in this repo
   is `@patch("market_data.universe.get_top_volume_symbols", return_value=[...])` or
   patching wherever the specific module imported the function (check
   `tests/test_universe.py` for both patterns already in use, and the `api_client`
   fixture pattern in `tests/conftest.py` for how other API-route tests are structured).
3. Re-run the full suite and confirm the wall-clock duration drops back down to roughly
   what it was before this whole feature (~150-200s is the expected ballpark — if it's
   still significantly higher, keep looking for another unmocked call site, don't stop
   at the first one you fix).

## Explicit non-goals

- Don't change the production behavior of `OpportunityScanner()`, `api/routes/scanner.py`,
  `decision/aggregator.py`, or `services/terminal_service.py` — this sprint is test-only.
- Don't touch `market_data/universe.py` itself unless you find an actual bug in it while
  investigating (if so, explain clearly and keep the fix minimal).
- No frontend changes.

## Acceptance criteria

- `pytest tests/ -q` full run duration is back down near its pre-sprint baseline
  (report the exact before/after numbers in your summary).
- 0 failures, same or higher pass count than the 1350-passing baseline.
- Your summary lists every test file you had to add mocking to, and confirms you
  searched all three call sites (scanner routes, aggregator, terminal_service), not
  just the first one you found.
