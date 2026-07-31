# Jules Workflow Rule

**No AI agent (Jules or otherwise) merges or pushes directly to `main`. Ever.**

## The rule

1. Jules always works on its own branch and opens a Pull Request against `main`. Jules never pushes directly to `main`, and `main` is protected on GitHub so this isn't optional (see setup below).
2. Before any PR is merged, Claude reviews the **actual diff** (`git diff` / the GitHub PR "Files changed" tab) — not Jules's own prose summary of what it did. Chat summaries from any AI agent are a claim, not evidence, until checked against the real change.
3. If a fix changes shared/business-logic constants (e.g. status enums, thresholds, weights) to make a test pass, Claude explicitly checks whether the *test* was wrong or the *code* was wrong — silently "fixing" one to match the other without that judgment call is not acceptable. Flag it back to the human if unclear.
4. Only after that review does the human give the final go-ahead to merge.

## Why

On 2026-07-31, Jules reported "all 10 remaining test failures fixed" including changing `database.py`'s `FINAL_STATUSES` to remove `CANCEL` from it — which is a real business-logic change (whether a cancelled trade counts as "done") made to satisfy a stale test assertion, not verified against how `FINAL_STATUSES` is actually used elsewhere (`execution/paper_executor.py` validates close-status input against it). This was caught only because the actual diff was checked instead of trusting the summary. The repo's own status/limitation docs were separately found to contain false "already fixed" claims for the same reason: nobody re-verified them against real code. Pattern: unverified AI-agent self-reports are not reliable enough to merge on their own.

## Standing instructions — paste this block at the top of every sprint given to Jules

```
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
   and what you found — "I checked X other call sites, none affected" or "X call site
   is affected, here's how I handled it."

3. Never modify a test's assertion to match broken/wrong code just to turn it green.
   If you believe the test itself is outdated or asserting the wrong thing, say so
   explicitly in your summary with your reasoning — don't silently rewrite it.

4. You must work on your own branch and open a Pull Request against `main`. Never
   push directly to `main` (it's also branch-protected, so this will be rejected
   regardless). Do not report a task as "done" or ask about merging until there is
   a real PR with a real diff — a chat summary of what you did is not sufficient for
   review or merge approval.

5. In your final summary, list the exact files you changed, one line per file
   describing the change and why — not just a narrative paragraph.
```

## Branch protection setup (GitHub, one-time, do via web UI — no CLI needed)

Repo: `github.com/mustafa78-bit/elite-decision-engine` → Settings → Branches → Add branch protection rule:

- Branch name pattern: `main`
- Require a pull request before merging: **on**
- Require approvals: **on**, at least 1
- Do not allow bypassing the above settings: **on** (so even the repo owner can't push straight to `main` by accident)
