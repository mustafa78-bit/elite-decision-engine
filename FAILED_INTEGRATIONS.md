# Failed and Partial Integrations Report

This report documents all production integrations categorized as **FAILED** or **PARTIAL** during our activation audit. Each entry includes the Root Cause, Risk, and Recommended Fix.

---

## 1. Hyperliquid Historical Funding Rates (`/fundingHistory`)

### Status
**PARTIAL**

### Root Cause
The `FundingCollector.fetch_funding_history` method in `market_data/funding/collector.py` sends a POST request with payload `{"type": "fundingHistory", "req": {"coin": symbol, "limit": limit}}` to `https://api.hyperliquid.xyz/info`.
The Hyperliquid production API has recently updated its schema and now strictly requires a `startTime` parameter (even if set to `0`) inside the `"req"` dictionary. Because the payload is missing this key, the upstream API returns `422 Client Error: Unprocessable Entity`.

### Risk
**Low-Medium.** Downstream sentiment scanners that rely on historical funding rate trends will receive an empty dataset. While the system stays completely stable and online due to defensive exception handling, the quality of scoring indicators is slightly degraded.

### Recommended Fix
Update the `fetch_funding_history` method in `market_data/funding/collector.py` to always pass `"startTime": 0` inside the `req` payload:
```python
payload = {
    "type": "fundingHistory",
    "req": {
        "coin": symbol.replace("USDT", ""),
        "limit": limit,
        "startTime": 0,
    },
}
```

---

## 2. Hyperliquid Open Interest (`/openInterests`)

### Status
**PARTIAL**

### Root Cause
The `OpenInterestCollector.fetch_all` method in `market_data/open_interest/collector.py` makes a POST request to `https://api.hyperliquid.xyz/info` with the body `{"type": "openInterests"}`.
The global openInterests API endpoint has been deprecated or changed in the Hyperliquid production API. Upstream returns `422 Failed to deserialize the JSON body into the target type`.

### Risk
**Low.** Scanners relying on open interest indicators will receive empty dataset results. The collector catches the exception cleanly and returns an empty `OpenInterestResult()` fallback, preventing any system crashes.

### Recommended Fix
Switch from the global deprecated `/openInterests` type to the newer `metaAndAssetCtxs` query type. This endpoint is highly reliable and contains openInterest values inside the second element of the returned array for all symbols:
```python
# In market_data/open_interest/collector.py
payload = {"type": "metaAndAssetCtxs"}
# Then map the openInterest from the response universe element for the requested coin.
```

---

## 3. AI Services — NVIDIA NIM

### Status
**PARTIAL**

### Root Cause
When the system is deployed without a valid `NVIDIA_API_KEY` environment variable, the authorization header is constructed as `Authorization: Bearer `. Upstream NVIDIA gateways reject this header with a signature or parsing error (`Illegal header value b'Bearer '` or HTTP 401).

### Risk
**Medium.** When unconfigured, AI-powered natural language explanations, council summaries, and briefing features are unavailable, forcing the UI to display fallback template descriptions.

### Recommended Fix
1. Validate that the `NVIDIA_API_KEY` is not empty before initiating requests.
2. If empty, short-circuit immediately without making the outbound HTTP request and return a structured offline fallback model. This reduces latency and avoids filling logs with bearer token parsing warnings.

---

## 4. Live Exchange API Connectivity — Binance

### Status
**PARTIAL**

### Root Cause
When Live Mode is enabled, outbound connection calls from inside server environments (such as standard US-based cloud hosting or sandbox environments) to `https://api.binance.com` are blocked with HTTP `451 Client Error: Unavailable for Legal Reasons` due to geographic IP restrictions.

### Risk
**High (in Live Mode only).** This halts live trade execution and live balance updates for users operating from US-restricted IP locations.

### Recommended Fix
1. Ensure the platform remains in **Paper Mode** (which does not make outbound network execution calls to Binance) by default.
2. In production deployment environments, restrict live Binance execution to servers provisioned in fully supported international cloud regions, or utilize API proxies.
