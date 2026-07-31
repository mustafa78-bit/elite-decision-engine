# Sprint 2/3: Journal missing-entry behavior (parallel-safe: only touches api/routes/journal.py — does not overlap with Sprint 1 or 3)

## Context

Run `pytest tests/ -q` first to confirm the current baseline before you start.

**This repo's own docs (`KNOWN_LIMITATIONS.md`, `TECHNICAL_DEBT.md`, `MASTER_BOOK.md`) are unreliable** — several "critical bug" claims in them were checked against actual code and found false or already fixed. Do not use those files as a source of truth. Verify everything against actual code and full tracebacks.

## Your task

`tests/test_api_routes.py::test_update_journal_missing` and `test_delete_journal_missing` expect a `404` when acting (PUT/DELETE) on a journal entry that doesn't exist, but the API currently returns `200`.

1. Read both failing tests in `tests/test_api_routes.py` to see the exact expected contract.
2. Read `api/routes/journal.py` — the PUT and DELETE handlers are likely not checking whether the journal entry exists before returning a success response.
3. Confirm the test's expectation (404 on missing resource) is correct product behavior — it is the standard REST convention, so unless you find explicit evidence elsewhere in the codebase that this route intentionally no-ops on missing IDs, fix the route to check existence and return 404 (FastAPI `HTTPException(status_code=404)`) when the entry isn't found.

## Acceptance criteria

- `tests/test_api_routes.py::test_update_journal_missing` and `test_delete_journal_missing` pass.
- No other currently-passing test regresses.
- Don't touch any other file outside `api/routes/journal.py` (and its direct service, only if the existence check truly needs to live there instead).
