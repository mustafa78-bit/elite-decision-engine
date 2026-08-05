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

5. Before claiming any test count/status, actually run `pytest tests/ -q` yourself
   and paste the real final line in your summary.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint: Wire TradeMemory into the actual paper trade lifecycle

## Context

`memory/trade_memory.py`'s `TradeMemory` class is fully built and genuinely DB-backed
(reads/writes go through `JournalEntry` rows, not just an in-memory cache — verify this
yourself by reading the file) — it stores entry reasoning, conditions, exit results, PnL,
lessons, and tags, and computes win-rate/stats. `execution/pipeline.py` already reads
from it (`trade_memory.list(limit=20)`) to build `memory_context` for decisions (recent
win/loss history for the same symbol+side).

**The problem**: nothing in the actual trading pipeline ever calls
`TradeMemory.record()` or `TradeMemory.close()`. Verify this yourself
(`grep -rn "trade_memory\.\|TradeMemory(" --include="*.py" .` outside `tests/` — as of
this writing it only appears in `execution/pipeline.py`, which only *reads* via
`.list()`). So the memory this is supposed to build up over time is permanently empty in
practice — the "learn from past trades" feature has never actually recorded a single
trade.

`database.py`'s `JournalEntry` model already has a `trade_id` column (nullable Integer)
intended to link a journal/memory entry back to the `Trade` row it came from — this is
the join key to use.

## Your task

1. In `execution/paper_executor.py`, find where trades actually open
   (`open_trade`/`open_trade_from_request`, ~line 82-150) and where they close
   (`close_trade`/`_close_trade_record`, ~line 218-400) — read these methods fully
   before changing anything.
2. Extend `TradeMemory.record()` in `memory/trade_memory.py` to accept an optional
   `trade_id: Optional[int] = None` parameter and set it on the created `JournalEntry`
   row (it already has the column, just isn't being set anywhere).
3. Wire `TradeMemory.record()` into the trade-opening path: after a `Trade` row is
   successfully created and has its `id`, call `TradeMemory().record(...)` with the
   real symbol, side, entry_price, an entry_reason (use whatever reasoning/signal
   context is available at that point — check what's already passed into
   `open_trade`/`open_trade_from_request`, don't invent data that isn't there), and
   `trade_id=<the new Trade's id>`.
4. Wire `TradeMemory.close()` into the trade-closing path: when a trade closes (TP hit,
   SL hit, manually closed, etc.), look up the matching `JournalEntry` by `trade_id`
   (a simple `session.query(JournalEntry).filter(JournalEntry.trade_id == trade.id).first()`
   is fine — don't over-engineer a new lookup method unless you have a good reason) and
   call `TradeMemory.close()` with the real exit_price, pnl, result (map the trade's
   close status to `"WIN"`/`"LOSS"` — check `_normalize_close_status` and how
   `FINAL_STATUSES` values like `TP_HIT`/`SL_HIT`/`CLOSED`/`CANCEL` should map; a
   cancelled trade probably isn't a WIN or LOSS, decide sensibly and explain your
   reasoning in the summary), and exit_reason.
5. Keep `lessons` simple for now — a short auto-generated string is fine (e.g. "Take
   profit hit as planned" / "Stop loss hit — entry thesis invalidated" /
   "Manually closed"), this doesn't need to be sophisticated yet.
6. Handle failures gracefully — if `TradeMemory.record()`/`.close()` fails for any
   reason, log it but do NOT let it block or fail the actual trade open/close operation.
   Trade execution must never depend on the memory write succeeding.

## Explicit non-goals

- Don't change `execution/pipeline.py`'s existing `memory_context` read logic — it
  should just start getting real data once this sprint lands, no code change needed
  there unless you find an actual bug in it.
- Don't build any UI for viewing trade memory/lessons — backend only.
- Don't attempt anything sophisticated for "lessons" generation (no LLM call, no
  pattern analysis) — that's future work, not this sprint.
- No frontend changes.

## Acceptance criteria

- Opening a paper trade creates a real `JournalEntry` via `TradeMemory.record()`, linked
  via `trade_id`.
- Closing a paper trade updates that same `JournalEntry` via `TradeMemory.close()` with
  real exit data.
- A memory-write failure never breaks or blocks the actual trade open/close operation.
- Add or update tests covering both the open-records-memory and close-updates-memory
  paths (check `tests/test_paper_executor.py` for the existing test structure/patterns
  to follow).
- `pytest tests/ -q` shows no new failures vs the current passing baseline (confirm the
  exact number yourself before you start).
