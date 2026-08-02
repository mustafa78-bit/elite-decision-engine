STANDING RULES (apply to this entire sprint):

1. Never trust this repo's own markdown docs (KNOWN_LIMITATIONS.md, TECHNICAL_DEBT.md,
   MASTER_BOOK.md, PROJECT_STATUS.md, etc.) as ground truth. They have repeatedly been
   found stale or simply wrong. Verify every claim against the actual current code
   before acting on it.

2. Never modify a test's assertion to match broken/wrong code just to turn it green.
   If you believe a test is outdated or asserting the wrong thing, say so explicitly
   in your summary with your reasoning.

3. You must work on your own branch and open a Pull Request against `main`. Never
   push directly to `main`. Do not report a task as "done" until there is a real PR
   with a real diff — a chat summary of what you did is not sufficient for review.

4. This sprint is intentionally scoped small and read-only on purpose. Do not expand
   it into a full trading-control bot — see explicit non-goals below. If you get
   stuck on one command, push what you have and say what's blocked.

5. Before claiming any test count/status, actually run `pytest tests/ -q` yourself
   and paste the real final line in your summary.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint: Telegram bot (MVP, read-only)

## Context

The user needs to reach NEXUS without being at a screen. `config.py` already has a
`TELEGRAM_TOKEN` placeholder read from env — nothing else related to Telegram exists in
the codebase yet (`notifications/dispatcher.py` handles other channels, check it for the
existing dispatcher pattern to stay consistent with, but it has no Telegram sender
today — verify this yourself, don't assume). This is a greenfield build.

**This is explicitly an MVP**: read-only status/briefing/Q&A. It must NOT be able to
place, modify, or cancel trades, or change any system configuration. See non-goals.

## Your task

1. Pick a Telegram bot library (`python-telegram-bot` is the standard choice — check
   it isn't already a near-duplicate of something in `requirements.txt`/`pyproject.toml`
   before adding it).
2. Build a bot service (new module, e.g. `services/telegram/bot.py` — organize
   consistently with how `services/ollo/` is structured) supporting these commands,
   using **existing** backend logic, not new duplicate logic:
   - `/status` — pulls from the same data `monitoring/health.py` / `/dashboard/hero`
     already expose. Don't reimplement health checks.
   - `/brief` — triggers the existing Ollo briefing generation
     (`services/ollo/ollo_service.py` / `services/ollo/briefing.py`) and sends the
     result as a message.
   - `/ask <question>` — routes the question through the existing `OLLOService.query()`
     path (same one the frontend's `/ollo/query` endpoint uses) and replies with the
     text response. If the response carries an `intent_route`, just mention it in text
     (e.g. "this relates to your portfolio") — do not attempt any navigation concept,
     that's a web-UI-only idea.
3. Wire bot startup into the existing app lifecycle sensibly — check `startup.py` and
   `api/main.py`'s `lifespan` for the pattern already used to start background tasks,
   and follow it rather than inventing a separate process model, unless you have a
   good reason (explain if so).
4. Handle the bot being unconfigured gracefully: if `TELEGRAM_TOKEN` is empty/unset,
   the bot must not crash the app on startup — log a warning and skip starting it,
   consistent with how `TELEGRAM_TOKEN not set` is already logged elsewhere at
   startup (check `startup.py`'s `StartupValidator` for the existing pattern).
5. Add tests for the new module following this repo's existing test conventions
   (see `tests/test_notification_dispatcher.py` for a comparable service test).

## Explicit non-goals — do not build these

- No trade execution, no position modification, no configuration changes reachable
  from Telegram. This bot is read-only, full stop.
- No two-way "commander" experience beyond the 3 commands above — no free-form chat
  loop beyond `/ask`, no persistent conversation memory across messages.
- No frontend changes.
- No webhook-based production deployment concerns (ngrok, public URL, etc.) — polling
  mode is fine for this MVP, note in your summary if you chose polling vs webhook and
  why.

## Acceptance criteria

- A bot module exists that responds to `/status`, `/brief`, and `/ask <question>` by
  calling existing backend logic, not reimplementing it.
- App starts up fine whether or not `TELEGRAM_TOKEN` is set.
- Tests exist for the new module and pass.
- `pytest tests/ -q` shows no new failures vs the 1325-passing baseline.
- Your summary explains how to actually run/test the bot locally (what env var to set,
  how to send it a test message).
