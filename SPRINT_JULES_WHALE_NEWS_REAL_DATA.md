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

4. This sprint is intentionally scoped to backend only, no frontend changes, to keep
   it small enough to actually complete. If you get stuck on one part (whale or
   news), push what you have and say what's blocked rather than nothing at all.

5. Before claiming any test count/status, actually run `pytest tests/ -q` yourself
   and paste the real final line in your summary.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint: Real whale + news data (MVP, zero paid APIs)

## Context

`market/intelligence/whale.py`'s `WhaleService` and `market/intelligence/news.py`'s
`NewsService` are currently **entirely fake** — `WhaleService.detect()` guesses "whale
activity" purely from volume/volatility score thresholds, and `NewsService.analyze()`
literally invents a headline like "`{symbol} moved {X}% in 24h`" from price data. Neither
touches any real external source. This is the core "AI has real market intelligence"
promise of the product and it's currently decorative.

Goal for this sprint: replace both with real, **free** data sources — no paid API
subscriptions, this is deliberately an MVP validation pass before spending money on
Whale Alert or similar (that's a later decision, out of scope here).

## Part 1 — Whale activity from real Binance market data

`exchange/binance/connector.py` already exists in this repo (`BinanceExchange` class) —
read it first to see what it already supports. Binance's public market-data REST
endpoints are free and need no API key for read-only data (klines, order book depth,
24hr ticker, open interest, funding rate).

1. Use real Binance data as a whale-activity proxy: unusually large single trades in
   recent trade history, abnormal order book depth imbalance, or sharp funding-rate /
   open-interest moves (check `market_data/funding/` and `market_data/open_interest/`
   for existing collector patterns you can reuse or call into — don't duplicate
   collector logic that already exists).
2. Rework `WhaleService.detect()` (or add a new method alongside it, your call, explain
   which in your summary) to compute its signals from this real data instead of the
   volume_score/volatility_score heuristic. Keep the existing return shape (list of
   dicts with `type`, `symbol`, `severity`, `description`, `confidence`, `timestamp`)
   so callers don't break — check `tests/test_intelligence*.py` and any route that
   calls `WhaleService` for the exact contract expected.
3. If Binance rate limits or data gaps make a specific detection unreliable, say so
   explicitly in your summary rather than silently faking a result.

## Part 2 — News sentiment from a real free source

1. Pick ONE of: a free-tier news API (e.g. CryptoPanic's free tier — check their docs
   for the actual free-tier request format, don't guess field names) or a public RSS
   feed from a major crypto news outlet. Explain which you picked and why in your
   summary.
2. Fetch recent headlines relevant to the asset being analyzed.
3. For sentiment scoring, reuse the **existing** NVIDIA NIM LLM integration already in
   this repo (`services/ai/nvidia_provider.py`, `services/ai/provider.py`) — do not
   add a new sentiment-analysis dependency or service. Send headlines to the existing
   provider and parse a sentiment label/score from its response.
4. Rework `NewsService.analyze()` to return real headlines + real LLM-derived sentiment
   instead of the fabricated price-based headline. Keep the existing return shape
   (list of dicts with `source`, `headline`, `sentiment`, `relevance`, `timestamp`) so
   `sentiment_score()` and any callers keep working.
5. Handle the case where the external news source is unreachable or rate-limited
   gracefully (log it, return an empty list) — don't crash the caller.

## Explicit non-goals

- No paid APIs, no new npm/pip dependencies beyond what's needed for the HTTP calls
  themselves (the project already has `requests` and `httpx` available — check before
  adding anything new).
- No frontend changes.
- Don't touch the Council agents (`council/whale_agent.py`, `council/news_agent.py`)
  unless you find they need a small adapter to consume the new data shape — if so,
  keep that change minimal and explain it.
- Don't wire real Telegram-channel scraping in this sprint — that was discussed as a
  future free option but is out of scope here; stick to Binance + the news source.

## Acceptance criteria

- `WhaleService` and `NewsService` return data derived from real external sources, not
  fabricated from price movement alone.
- Existing tests for these services still pass, or are updated to reflect the new
  (still-real) behavior with your reasoning stated.
- `pytest tests/ -q` shows no new failures vs the 1325-passing baseline.
- Your summary states exactly which free data sources were used and any real
  limitations found (rate limits, coverage gaps).
