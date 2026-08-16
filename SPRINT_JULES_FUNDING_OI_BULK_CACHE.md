STANDING RULES (apply to this entire task):

1. Never trust this repo's own markdown docs (KNOWN_LIMITATIONS.md, TECHNICAL_DEBT.md,
   any *_REPORT.md/*_READINESS.md, etc.) as ground truth. Verify every claim against
   the actual current code before acting on it.

2. Never modify a test's assertion to match broken/wrong code just to turn it green.

3. Cut your branch off the current tip of `main`: `git fetch origin && git checkout -b
   <your-branch> origin/main`. Verify with `git log origin/main..HEAD --oneline` right
   before you push — it must show ONLY your own new commits. Open a Pull Request
   against `main`. Never push directly to `main`.

4. Before claiming any test count/status, actually run the FULL suite yourself —
   `pytest tests/ -q` — not just a subset, and paste the real final line in your
   summary.

5. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Task: cache the Hyperliquid bulk funding/open-interest fetch so it stops being hit N times per scan

## Background — verify this yourself, don't take this description as ground truth

Confirm yourself: `market_data/funding/collector.py`'s `FundingCollector.fetch_all()` and
`market_data/open_interest/collector.py`'s `OpenInterestCollector.fetch_all()` both POST
to the exact same Hyperliquid endpoint — `BASE_URL = "https://api.hyperliquid.xyz/info"`
with `{"type": "metaAndAssetCtxs"}` — and this single call already returns funding/OI data
for *every* symbol on the exchange in one response (`meta["universe"]` +
`assetCtxs`, matched by index). It is a bulk "fetch everything" endpoint, not a per-symbol
one. Neither collector caches this response today — every call is a fresh network hit.

Now trace the real call chain that reaches these two methods (read the actual code, don't
take this description as ground truth):

- `scanner/core.py`'s `Scanner.scan()` loops over the full fixed coin universe (currently
  25 symbols, see `config.FIXED_COIN_UNIVERSE`) and calls `self._scan_symbol(symbol,
  timeframe)` for each one.
- `_scan_symbol()` calls `self.market_service.get_asset(symbol, timeframe)`
  (`market/services/market_data.py`).
- `MarketDataService.get_asset()` caches its *final* result per `(symbol, timeframe)` via
  `self.cache.make_key("asset", symbol, timeframe)` — but that cache key is per-symbol, so
  it cannot dedupe anything *across* the 25 different symbols in a single scan pass. On the
  way to building that per-symbol result, it calls `self.intelligence.enrich(asset)`
  (line ~144) unconditionally for every symbol.
- `IntelligenceService.enrich()` (`market/intelligence/service.py`) calls
  `self._get_funding(symbol)` → `self.funding_collector.fetch_for_symbol(coin)` → which
  internally calls `fetch_all()` — and `self._get_open_interest(symbol)` →
  `self.oi_collector.fetch_with_trend(coin)` → `fetch_for_symbol()` → `fetch_all()`.

So one `Scanner.scan()` pass over 25 symbols currently fires up to **50 separate HTTP
POSTs** to the same Hyperliquid bulk endpoint, all requesting and receiving the exact same
full-universe snapshot, just to read out a different symbol's row each time. This is the
confirmed root cause of the Scanner page (`GET
/scanner/category/top-movers?n=20&timeframe=1h&market=futures`) hanging/timing out in a
live check of this app — Hyperliquid's own rate limiting kicks in against this burst of
near-identical requests fired within milliseconds of each other.

This is not limited to the scanner path. Verify yourself (grep for
`FundingCollector\(\)|OpenInterestCollector\(\)` across the whole repo) that these two
classes are also independently constructed, with zero sharing between them, in at least:
`market_data/intelligence.py`, `api/routes/funding.py`, `api/routes/open_interest.py`,
`market/provider/hyperliquid.py` (inside `HyperliquidProvider` itself), and
`market/intelligence/whale.py`. Every one of these currently makes its own fresh,
unshared, uncached bulk fetch.

Note this repo already has a working precedent for exactly this kind of fix:
`market/services/market_data.py`'s `_TIMEFRAME_TTL_SECONDS` / `CacheManager` pattern (used
by `get_ohlcv()`) caches per-key results with a TTL instead of refetching every call.
Follow that spirit here, but note the shape is different: `CacheManager` is keyed by
`(symbol, timeframe)` and lives on one shared `MarketDataService` instance, whereas
`FundingCollector`/`OpenInterestCollector` are constructed fresh, independently, in many
unrelated places with no shared instance to hang a per-instance cache off of. Design
accordingly (see "What to build" below).

Do **not** assume this should instead be migrated onto `MultiProvider`
(`market/provider/multi.py`) the way `BinanceProvider` Step 3 migrated per-symbol OHLCV
calls — verify why that doesn't fit: `MultiProvider` exists to split *per-symbol* calls
across providers/rate limits, but `metaAndAssetCtxs` is a *bulk* "every symbol in one call"
endpoint. The fix here is caching the bulk response, not routing individual symbol
requests anywhere.

## What to build

Add a TTL-based cache **inside** `FundingCollector.fetch_all()` and
`OpenInterestCollector.fetch_all()` themselves, so every current and future caller of
either class benefits automatically without any caller needing to change.

1. The cache must be shared across *all instances* of the same collector class within one
   process, not just within a single instance — verify why: `IntelligenceService.__init__`
   builds one `FundingCollector()`/`OpenInterestCollector()` pair that's reused for the
   scanner's 25-symbols-per-scan loop (so instance-level caching *would* fix that specific
   case), but `api/routes/funding.py`, `api/routes/open_interest.py`,
   `market/provider/hyperliquid.py`, and `market/intelligence/whale.py` each construct
   their *own separate* instance — only a cache shared at the class level (e.g. a class
   variable, or a module-level cache object) collapses redundant calls across those too.
   Since this module is imported once per Python process, a class-level attribute is
   genuinely process-wide — confirm this is true for how the app actually runs (single
   `uvicorn` worker per `api/main.py`, check `requirements.txt`/deploy config for whether
   multiple workers are ever used) and note your finding in the PR.
2. Pick a TTL that's safe for the real data: funding rates update roughly hourly on real
   exchanges, open interest more often but still not sub-second. Something like 30 seconds
   collapses an entire scan's worth of near-simultaneous calls into one real network hit
   while staying well within "fresh enough" for this data. Put it as a named class constant
   (e.g. `_CACHE_TTL_SECONDS = 30`) so it's easy to find and tune later, not a magic number.
3. Cache only the raw `fetch_all()` result (the parsed `FundingResult`/`OpenInterestResult`
   plus the fetch timestamp used to decide staleness) — do **not** cache or otherwise touch
   `OpenInterestCollector`'s `self._history` deque / `fetch_with_trend()`'s trend
   derivation. That mechanism intentionally accumulates real history across genuinely
   separate calls over time to compute a trend; it must keep being fed by real (even if
   now-cached) snapshots, not be short-circuited itself.
4. On a cache hit (within TTL), return the cached parsed result without touching
   `self._session.post(...)` at all — this is the actual fix, since the network call (and
   its 3x retry/backoff on failure) is what burns time and trips rate limits.
5. On a cache miss or TTL expiry, fetch for real, update the cache, and return the fresh
   result — same as today's behavior otherwise (including the existing error handling: a
   failed fetch should not poison the cache with a bad/empty result, and should not corrupt
   sharing between instances).
6. No config flag or env var needed — this is an internal implementation detail, not a
   feature to toggle. Keep it simple: a class-level `(timestamp, result)` slot guarded by a
   plain `time.time()` comparison. This process has no real concurrent-write hazard here
   (note if you find otherwise — e.g. genuinely concurrent async paths racing to populate
   it — and handle it, but don't add locking machinery speculatively if a single check is
   sufficient).

## Explicitly out of scope

- Do not touch `MultiProvider`, `BinanceProvider`, or any per-symbol OHLCV path — unrelated,
  see the Background section for why this is architecturally a different problem.
- Do not modify `OpenInterestCollector`'s `_history`/`fetch_with_trend()`/`detect_oi_trend`
  trend-derivation logic, only the underlying `fetch_all()` network call it depends on.
- Do not change the funding/OI response shape, field names, or any downstream consumer's
  parsing logic.
- Do not modify `api/routes/funding.py`, `api/routes/open_interest.py`,
  `market/provider/hyperliquid.py`, `market/intelligence/service.py`,
  `market/intelligence/whale.py`, or `market_data/intelligence.py` — the whole point is
  that none of these callers need to change; they benefit automatically once the cache
  lives inside the two collector classes.
- Do not add a new external cache dependency (Redis, etc.) — a simple in-process
  class-level cache is sufficient here, matching this repo's existing `CacheManager`'s own
  in-process style.
- Do not touch the frontend.

## Test plan expectations

- Unit test: mock/count calls to the collector's underlying `self._session.post` (or
  `requests.Session.post`), call `fetch_all()` twice back-to-back on the *same* instance,
  assert exactly 1 real HTTP call happened and both calls returned equal data.
- Unit test: same as above but across **two separate instances** of the same collector
  class (`FundingCollector()` twice / `OpenInterestCollector()` twice) — this is the test
  that actually proves the fix covers the cross-call-site redundancy described in the
  Background section, not just the scanner's single-instance reuse.
- Unit test: after the TTL window elapses (monkeypatch `time.time` forward, or use a very
  small TTL injected for the test), a subsequent call DOES trigger a new real HTTP call.
- Unit test: a failed fetch (mock `requests.RequestException`) does not populate the cache
  with a bad/empty result that then gets incorrectly served as if it were a real cached
  snapshot on the next call.
- Find and run this repo's existing tests for these two collectors (search for existing
  test files covering `FundingCollector`/`OpenInterestCollector` — don't assume names) and
  confirm they still pass unmodified (or update them only if they were asserting the old
  "always makes a fresh call" behavior, and say so explicitly in your PR).
- Run the full backend suite (`pytest tests/ -q`) and paste the real final line in your
  summary.
