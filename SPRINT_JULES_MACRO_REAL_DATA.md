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
   it small enough to actually complete. If you get stuck on one part, push what you
   have and say what's blocked rather than nothing at all.

5. Before claiming any test count/status, actually run `pytest tests/ -q` yourself
   and paste the real final line in your summary.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint: Real data for Council's Macro agent inputs (Fear & Greed + Liquidity)

## Context

`council/macro_agent.py`'s `MacroAgent` itself is fine — it just reads whatever's in the
`intelligence_bundle` it's given (`funding`, `open_interest`, `fear_greed`, `liquidity`,
`exchange_flow`). `funding` and `open_interest` are already real (backed by
`market_data/funding/collector.py` and `market_data/open_interest/collector.py`, which
call Hyperliquid). But three of the five inputs are entirely fabricated from other
in-app scores, not from any real external source:

- `market/intelligence/fear_greed.py`'s `FearGreedService.compute()` — computed purely
  from RSI/trend/volatility already known internally. Its own docstring says "computed
  from market conditions when no external API is available."
- `market/intelligence/liquidity.py`'s `LiquidityContextAnalyzer.analyze()` — computed
  from volume score and ATR, no real order-book data.
- `market/intelligence/exchange_flow.py`'s `ExchangeFlowService.analyze()` — computed
  from volume/volatility score, no real on-chain flow data.

## Part 1 — Fear & Greed from the real, free, official API

[alternative.me](https://alternative.me/crypto/fear-and-greed-index/) publishes the
actual Crypto Fear & Greed Index via a free public JSON API
(`https://api.alternative.me/fng/`) — no API key required, no rate limit documented for
reasonable use. This is THE standard source everyone means when they say "fear and greed
index" — verify the exact response shape yourself by checking the endpoint (or its docs)
before writing the parser, don't guess field names.

1. Rework `FearGreedService.compute()` (or add a new method, your call — explain which
   in your summary) to fetch the real index value/classification from this API.
2. Keep the existing return shape (`value`, `label`, `signals`, `confidence`,
   `timestamp`) so `MacroAgent` doesn't need to change. Map the API's classification
   strings (it uses "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed") to this
   codebase's existing label constants (`EXTREME_FEAR`, `FEAR`, `NEUTRAL`, `GREED`,
   `EXTREME_GREED` — check `FEAR_GREED_MAP` in `council/macro_agent.py` for the exact
   strings expected).
3. If the API call fails (network error, unexpected shape), fall back to the existing
   RSI/trend/volatility heuristic rather than crashing — log it, don't hide it.

## Part 2 — Liquidity from real Binance order book depth

`market/intelligence/whale.py`'s `WhaleService` (already updated in a prior sprint) has
a `_binance_request` helper that fetches `/api/v3/depth` for whale-wall detection — reuse
that same pattern (don't duplicate the multi-host-fallback request logic; either import
and reuse `WhaleService`'s helper or factor it into a small shared utility if that's
cleaner — your call, explain which in your summary).

1. Fetch real order book depth for the symbol being analyzed.
2. Compute a genuine liquidity measure from it — e.g. total depth within some percentage
   of the mid-price (tighter spread + more depth = higher liquidity), not a guess from
   volume/ATR.
3. Keep the existing return shape (`symbol`, `score`, `level`, `signals`, `timestamp`) so
   `MacroAgent` doesn't need to change.
4. Fall back to the existing volume/ATR heuristic if the real data call fails.

## Explicit non-goals

- Do NOT attempt to make `exchange_flow.py` "real" — genuine on-chain exchange
  inflow/outflow data requires a paid service (Glassnode, CryptoQuant, etc.) with no
  good free equivalent. Leave it as-is, but add a one-line comment at the top of the
  file stating clearly that it's a heuristic proxy, not real on-chain data, so nobody
  mistakes it for the real thing later.
- No paid APIs, no new dependencies beyond what's needed for HTTP calls (the project
  already has `requests`).
- No frontend changes.
- Don't touch `council/macro_agent.py` itself unless the return shape of one of the two
  services above genuinely needs to change — if so, keep the change minimal and explain
  it clearly.

## Acceptance criteria

- `FearGreedService` returns the real index from alternative.me, with graceful fallback
  to the heuristic on failure.
- `LiquidityContextAnalyzer` returns a liquidity measure derived from real Binance order
  book depth, with graceful fallback to the heuristic on failure.
- `exchange_flow.py` has an honest comment marking it as a heuristic proxy, unchanged
  otherwise.
- `pytest tests/ -q` shows no new failures vs the 1339-passing baseline.
- Your summary states exactly which endpoints were used and any real limitations found.
