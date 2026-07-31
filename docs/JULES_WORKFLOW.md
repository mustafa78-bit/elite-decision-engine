# Jules Workflow Rule

**No AI agent (Jules or otherwise) merges or pushes directly to `main`. Ever.**

## The rule

1. Jules always works on its own branch and opens a Pull Request against `main`. Jules never pushes directly to `main`, and `main` is protected on GitHub so this isn't optional (see setup below).
2. Before any PR is merged, Claude reviews the **actual diff** (`git diff` / the GitHub PR "Files changed" tab) — not Jules's own prose summary of what it did. Chat summaries from any AI agent are a claim, not evidence, until checked against the real change.
3. If a fix changes shared/business-logic constants (e.g. status enums, thresholds, weights) to make a test pass, Claude explicitly checks whether the *test* was wrong or the *code* was wrong — silently "fixing" one to match the other without that judgment call is not acceptable. Flag it back to the human if unclear.
4. Only after that review does the human give the final go-ahead to merge.

## Why

On 2026-07-31, Jules reported "all 10 remaining test failures fixed" including changing `database.py`'s `FINAL_STATUSES` to remove `CANCEL` from it — which is a real business-logic change (whether a cancelled trade counts as "done") made to satisfy a stale test assertion, not verified against how `FINAL_STATUSES` is actually used elsewhere (`execution/paper_executor.py` validates close-status input against it). This was caught only because the actual diff was checked instead of trusting the summary. The repo's own status/limitation docs were separately found to contain false "already fixed" claims for the same reason: nobody re-verified them against real code. Pattern: unverified AI-agent self-reports are not reliable enough to merge on their own.

## Branch protection setup (GitHub, one-time, do via web UI — no CLI needed)

Repo: `github.com/mustafa78-bit/elite-decision-engine` → Settings → Branches → Add branch protection rule:

- Branch name pattern: `main`
- Require a pull request before merging: **on**
- Require approvals: **on**, at least 1
- Do not allow bypassing the above settings: **on** (so even the repo owner can't push straight to `main` by accident)
