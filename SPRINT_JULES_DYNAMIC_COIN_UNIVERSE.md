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

4. This sprint is intentionally scoped small on purpose — large multi-file sprints on
   this project repeatedly fail to complete. Stay inside the scope below. If you get
   stuck, push what you have and say what's blocked.

5. Before claiming any test count/status, actually run `pytest tests/ -q` yourself
   and paste the real final line in your summary.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint: Dynamic coin universe (top N by Binance 24h volume)

## Context

`scanner/core.py`'s `OpportunityScanner` currently only scans a hardcoded list of 3
symbols: `_DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]` (see `__init__`, line
~48: `self.symbols = symbols or _DEFAULT_SYMBOLS`). Decision made: replace this with a
**dynamic universe of the top N coins by 24h trading volume on Binance**, not a literal
"every coin Binance lists" — most of the long tail is illiquid and would produce noisy/
unreliable signals (whale-detection heuristics in particular assume a liquid market).

## Your task

1. Fetch Binance's `/api/v3/ticker/24hr` endpoint **with no symbol parameter** — this
   returns 24hr stats for every symbol in a single request (much more efficient than N
   individual calls). Verify the actual response shape yourself before parsing it, don't
   guess field names (you want the quote-volume field, likely `quoteVolume`).
2. Filter to USDT-quoted pairs only (symbols ending in `USDT`), sort by 24h quote volume
   descending, take the top N.
3. Add `COIN_UNIVERSE_SIZE` to `config.py` (default `100`, read from env var so it's
   adjustable without a code change: `int(os.getenv("COIN_UNIVERSE_SIZE", "100"))`).
4. Build this as a small new module (e.g. `market_data/universe.py` — pick a location
   consistent with existing `market_data/` conventions) with a function/class that
   returns the current top-N symbol list. **Cache the result with a refresh interval**
   (e.g. 1 hour, make it a constant) rather than re-fetching on every call — this data
   doesn't need to be real-time fresh, and re-fetching constantly wastes rate-limit
   budget for no benefit. If the Binance call fails, fall back to the last successfully
   cached list, or to the original 3-symbol hardcoded list if there's no cache yet at
   all — never crash the caller.
5. Wire this into `OpportunityScanner.__init__` so `self.symbols` defaults to this
   dynamic universe when no explicit `symbols` list is passed in, instead of
   `_DEFAULT_SYMBOLS`. Keep `_DEFAULT_SYMBOLS` itself as the final hardcoded fallback
   inside your new universe provider (see point 4), don't delete it.

## Explicit non-goals

- Do NOT try to solve rate-limiting for the *per-symbol* analysis work that happens
  once the universe is scanned (whale detection, indicators, etc. still run per-symbol
  and that's a separate, bigger concern) — this sprint is only about building the
  symbol *list* efficiently. If you notice the per-symbol scan loop will need real
  changes to handle 100 symbols instead of 3 (rate limits, timing), note it clearly in
  your summary as a follow-up concern — don't try to fix it in this sprint.
- Don't touch `market/intelligence/whale.py` or `news.py`'s per-symbol logic.
- No frontend changes.
- No paid APIs, no new dependencies beyond what's needed for the HTTP call (the project
  already has `requests`).

## Acceptance criteria

- A new module provides the current top-N (default 100, configurable via
  `COIN_UNIVERSE_SIZE`) Binance USDT pairs by 24h volume, cached with a sensible refresh
  interval, with a safe fallback chain (cache → hardcoded 3-symbol list) if the API call
  fails.
- `OpportunityScanner` uses this dynamic universe by default instead of the hardcoded
  3-symbol list, while still accepting an explicit `symbols` override for tests/callers
  that need one.
- `pytest tests/ -q` shows no new failures vs the current passing baseline (confirm the
  exact number yourself before you start).
- Your summary explicitly flags whether/how much the per-symbol scan loop's rate-limit
  behavior needs follow-up work now that the universe can be ~30x larger.
