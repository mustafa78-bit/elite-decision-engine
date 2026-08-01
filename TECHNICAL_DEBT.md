# Technical Debt & Known Issues

*Last verified against code: 2026-08-01. Every item below (both resolved and remaining) was checked directly against the current source. Several items previously listed here as "critical pre-production blockers" (`ConfidenceEngine` double-scaling, `ATRr_14` indicator typo, missing `pandas_ta` dependency, confidence hardcoded to 0.0 in `DecisionPipeline`, no filter chain wired into the pipeline) were re-checked and found to be false or already fixed — they have been removed rather than carried forward unverified.*

## Recently resolved (2026-07-31 session)

| ID | Issue | Status |
|----|-------|--------|
| LG1 | `logging_config.py`'s `_SensitiveDataFilter` stringified every log argument (including ints/floats) before redaction, breaking every `%d`/`%f` format specifier with `TypeError: %d format: a real number is required, not str` | ✅ Fixed — only string args are redacted now, non-string args pass through unchanged. This was the root cause of ~29 scattered-looking test failures across unrelated modules (`api/websocket/manager.py`, `council/consensus.py`, `services/coordinator_service.py`, `monitoring/health.py`) |
| RT1 | `api/routes/paper.py` (22 endpoints: `/paper/orders`, `/paper/trades`, `/paper/positions`, `/paper/summary`) existed but was never imported/registered in `api/main.py` — fully unreachable in the running app | ✅ Fixed — router wired in |
| RT2 | `api/routes/simulator.py` (25 endpoints) and the frontend `MarketSimulator.tsx` page existed but neither was wired into the running app or the frontend router, and the code wasn't even committed to git | ✅ Fixed — backend router registered, frontend route added, committed |
| DB2 | `session_scope()` context manager referenced by tests but missing from `database.py` | ✅ Fixed — restored |
| DB3 | `FINAL_STATUSES` was missing `CANCEL`, causing a stale test to pass with the wrong size (3 instead of 4) | ✅ Fixed — `CANCEL` confirmed correct (a cancelled trade is a final state), the test was updated, not the constant |
| WS1 | `services/widget_service.py`'s `_kpi_widget`/`_portfolio_widget`/`_monitoring_widget` didn't accept `**kwargs`, causing `TypeError` when routes passed extra params like `limit` | ✅ Fixed |
| JR1 | `api/routes/journal.py` PUT/DELETE on a missing entry already correctly returned 404 — a stale test asserted 200 instead | ✅ Fixed — test corrected to match the (already correct) code |
| INT1 | `market/intelligence/whale.py`'s `WhaleService` and `market/intelligence/news.py`'s `NewsService` were entirely simulated (fake headlines generated from price movement, whale signals guessed from volume score) | ✅ Fixed — whale activity now derived from real Binance trades/depth/funding/open-interest data (with fallback to the old heuristic if the real data call fails); news now fetched from real CoinTelegraph/CoinDesk RSS feeds with sentiment classified by the existing NVIDIA NIM LLM provider. Zero new paid dependencies. |
| TG1 | No way to reach NEXUS without the web UI | ✅ Added — read-only Telegram bot (`services/telegram/bot.py`): `/status`, `/brief`, `/ask`, chat_id whitelist, HTML-safe message chunking |
| CI1 | Frontend job in CI only ran `npm run build`, no test step | ✅ Fixed — `npm run test` added to `.github/workflows/ci.yml` |

## Remaining

### High priority

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| MC5 | No integrated live signal source for the scanner | `scanner/` | Scanner operates on paper/mock data only, not a live feed |
| MAC1 | Council's Macro agent not verified against a real data source (unlike Whale/News, fixed 2026-07-31) | `council/macro_agent.py` | Possible remaining stub/heuristic macro signal — needs the same verification pass Whale/News got |

### Medium priority

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| DB1 | No ForeignKey constraint on `Trade.signal_id` | `database.py` | Orphaned trades possible |
| RL1 | No per-route rate limiting (only global) | `api/rate_limit.py` | Susceptible to abuse on specific endpoints |
| JW1 | JWT key 30 bytes (< 32 recommended for HS256) | `.env` (not committed — check the real deployment value) | PyJWT `InsecureKeyLengthWarning`, weaker HMAC security margin |
| UT1 | `datetime.utcnow()` usage in several model default factories | `strategies/base.py`, `market/models/asset.py`, `market/models/ohlcv.py`, `exchange/models.py` | Deprecation warnings now, will break in a future Python version |
| TG2 | Telegram bot has no per-user rate limiting beyond the chat_id whitelist | `services/telegram/bot.py` | A whitelisted user could spam `/ask` and burn LLM request budget |

### Low priority

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| LC1 | Empty `__init__.py` files across many package directories | Multiple dirs | Minor maintenance clutter |
| LC2 | Legacy test files with zero assertions | `tests/` | False sense of coverage |

---

## Summary

| Severity | Count | Notes |
|----------|-------|-------|
| Resolved this session (2026-07-31) | 10 | LG1, RT1, RT2, DB2, DB3, WS1, JR1, INT1, TG1, CI1 |
| High (remaining) | 2 | MC5, MAC1 |
| Medium (remaining) | 5 | DB1, RL1, JW1, UT1, TG2 |
| Low (remaining) | 2 | LC1, LC2 |
