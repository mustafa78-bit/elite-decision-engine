# Market Intelligence Platform (MIP)

**Date:** 2026-07-10  
**Status:** COMPLETE — Layer built alongside existing `market_data/`.  
**Tests:** 830 passing (784 existing + 46 new MIP tests), 1 skipped, 0 regressions.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONSUMERS                                    │
│  Decision Engine  │  Scanner  │  Dashboard  │  Risk  │  Portfolio   │
│  AI  │  API  │  Future Modules (News, Whale, Terminal)              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MarketDataService (market/services/)               │
│                                                                      │
│  Single entry point for ALL market data.                             │
│  All future modules consume data through this service.               │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Provider │ │  Cache   │ │Indicator │ │  Feature │ │   Context    │
│  Layer   │ │ Manager  │ │ Service  │ │  Store   │ │   Service    │
│market/   │ │market/   │ │market/   │ │market/   │ │market/       │
│provider/ │ │cache/    │ │indicators│ │features/ │ │context/      │
└────┬─────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Data Providers (market/provider/)                  │
│                                                                      │
│  HyperliquidProvider  │  BinanceProvider  │  Future Providers       │
│  (wraps existing      │  (wraps existing  │  (pluggable adapter)    │
│   HyperliquidCollector)│  BinanceExchange)│                         │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│            EXISTING LAYER (unchanged, backward compatible)           │
│                                                                      │
│  market_data/  —  continues to work. All existing tests pass.        │
│  All existing code can migrate to MIP incrementally.                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Map

### `market/provider/`
| File | Purpose |
|---|---|
| `base.py` | `DataProvider` protocol + `OHLCVResult` dataclass |
| `hyperliquid.py` | `HyperliquidProvider` wrapping existing `HyperliquidCollector`, `FundingCollector`, `OpenInterestCollector` |

### `market/cache/`
| File | Purpose |
|---|---|
| `manager.py` | `CacheManager` — thread-safe in-memory cache with per-key TTL, pattern invalidation, `get_or_set` factory pattern |

### `market/indicators/`
| File | Purpose |
|---|---|
| `service.py` | `IndicatorService` — compute indicators once, cache results, reuse across all consumers |

### `market/features/`
| File | Purpose |
|---|---|
| `store.py` | `FeatureStore` — convert numeric indicators to categorical features (Trend, Momentum, Risk, Liquidity, Volatility Class, Regime Score) |

### `market/context/`
| File | Purpose |
|---|---|
| `service.py` | `ContextService` — BTC context, market session (Asian/London/NY), funding state, global context bundle |

### `market/models/`
| File | Purpose |
|---|---|
| `asset.py` | `Asset` + `AssetMetadata` — unified asset model for all modules |
| `ohlcv.py` | `OHLCVData` — typed wrapper around OHLCV DataFrame |

### `market/services/`
| File | Purpose |
|---|---|
| `market_data.py` | `MarketDataService` — single entry point; coordinates provider, cache, indicators, features, context into enriched `Asset` objects |

---

## 3. Asset Model

The `Asset` model is the universal data container:

```python
@dataclass
class Asset:
    symbol: str
    metadata: AssetMetadata    # exchange, base/quote, decimals
    price: float
    ohlcv: pd.DataFrame
    indicators: dict           # ema20, ema50, rsi, atr, etc.
    features: dict             # trend, momentum, risk, liquidity
    context: dict              # btc, session, funding
    news: list                 # placeholder for News module
    whales: list               # placeholder for Whale module
    timestamp: datetime
```

Future modules enrich the Asset:
```
Asset.news    ← populated by News Scanner
Asset.whales  ← populated by Whale Tracker
Asset.features ← enriched by AI models
```

---

## 4. Backward Compatibility Strategy

The existing `market_data/` package is **completely unchanged**. All 784 existing tests pass without modification.

| Strategy | Details |
|---|---|
| **Alongside** | MIP is a new layer, not a replacement. Both coexist. |
| **Delegation** | `HyperliquidProvider` wraps existing `HyperliquidCollector`, `FundingCollector`, `OpenInterestCollector` |
| **Incremental Migration** | Modules can switch from `market_data.X` to `market.services.MarketDataService` one at a time |
| **No Breaking Changes** | Zero imports changed, zero tests modified |

**Migration path for any module:**
```python
# OLD:
from market_data.collector import HyperliquidCollector
collector = HyperliquidCollector()
df = collector.get_ohlcv("BTC", "1h")

# NEW:
from market.services import MarketDataService
mds = MarketDataService()
asset = mds.get_asset("BTC")
df = asset.ohlcv
price = asset.price
indicators = asset.indicators
features = asset.features
```

---

## 5. Key Improvements

### 5.1 Single Source of Truth
Before MIP, `HyperliquidCollector` was instantiated 15+ times across the codebase. Each consumer independently fetched and processed the same data. MIP centralizes:

- **Data fetching** → `HyperliquidProvider` (single point of API access)
- **Caching** → `CacheManager` (no duplicated API calls)
- **Indicator computation** → `IndicatorService` (compute once, cache for all)
- **Feature extraction** → `FeatureStore` (consistent categorical features)
- **Market context** → `ContextService` (BTC, sessions, funding state)

### 5.2 Cache Efficiency
| Before | After |
|---|---|
| No shared cache | `CacheManager` with configurable TTL |
| Each consumer fetches same data | First fetch caches; all others reuse |
| No invalidation | Pattern-based invalidation |

### 5.3 Indicator Efficiency
| Before | After |
|---|---|
| 10+ places compute `IndicatorEngine.calculate(df)` | `IndicatorService.get_indicators()` computes once |
| `VolatilityEngine`, `VolumeEngine` called separately | All computed and cached together |

### 5.4 Consistent Feature Engineering
Before MIP, feature extraction was ad-hoc in each module. MIP's `FeatureStore` provides consistent categorical features:
- Trend: `BULLISH / MILD_BULLISH / NEUTRAL / MILD_BEARISH / BEARISH`
- Momentum: `STRONG / NEUTRAL / WEAK / OVERBOUGHT / OVERSOLD`
- Risk: `LOW / MEDIUM / HIGH`
- Liquidity: `HIGH / MEDIUM / LOW / UNKNOWN`
- Volatility: `LOW / NORMAL / HIGH / EXTREME`

### 5.5 Regime Score
The `FeatureStore._regime_score()` combines trend, momentum, and risk into a single `[0.0, 1.0]` score. This replaces ad-hoc scoring logic spread across modules.

---

## 6. API Reference

### MarketDataService

```python
mds = MarketDataService()

# Raw data
df = mds.get_ohlcv("BTC", "1h", 500)
ticker = mds.get_ticker("BTC")
funding = mds.get_funding("ETH")
oi = mds.get_open_interest("SOL")

# Enriched asset
asset = mds.get_asset("BTC")              # single
assets = mds.get_assets(["BTC", "ETH"])    # batch

# Convenience
price = mds.get_price("BTC")
indicators = mds.get_indicators("BTC")
features = mds.get_features("BTC", "1h", "LONG")
context = mds.get_context()

# Cache management
mds.invalidate_asset("BTC")
mds.invalidate_all()
```

### CacheManager

```python
cache = CacheManager(default_ttl=60)  # seconds

cache.set("key", value)
cache.set("key", value, ttl=30)       # per-key TTL

cache.get("key")                       # None if missing/expired
cache.get_or_set("key", factory_fn)    # compute-on-miss

cache.invalidate("key")
cache.invalidate_pattern("ohlcv:")     # invalidate all OHLCV keys
cache.clear()
```

### IndicatorService

```python
svc = IndicatorService()

indicators = svc.get_indicators("BTC", "1h", df)
# Returns: {ema20, ema50, ema200, rsi, atr,
#           volatility, volatility_score, volume_score}

values = svc.get_indicator_values("BTC", "1h", df)
# Returns: only numeric values

svc.invalidate("BTC", "1h")
```

### FeatureStore

```python
store = FeatureStore()
features = store.extract(indicators, side="LONG")
# Returns: {trend, momentum, risk, liquidity,
#           volatility_class, regime_score}
```

### ContextService

```python
ctx = ContextService()

btc = ctx.get_btc_context()          # {btc_price, btc_trend, ...}
session = ctx.get_market_session()    # "ASIAN" | "LONDON" | "NY"
funding = ctx.get_funding_state()     # {funding_rate, state}
bundle = ctx.get_context()            # all of the above
```

---

## 7. Test Coverage

| Module | Tests | File |
|---|---|---|
| Asset Model | 5 | `tests/market/test_asset_model.py` |
| CacheManager | 10 | `tests/market/test_cache_manager.py` |
| FeatureStore | 10 | `tests/market/test_feature_store.py` |
| IndicatorService | 4 | `tests/market/test_indicator_service.py` |
| HyperliquidProvider | 5 | `tests/market/test_hyperliquid_provider.py` |
| MarketDataService | 7 | `tests/market/test_market_data_service.py` |
| ContextService | 5 | `tests/market/test_context_service.py` |
| **Total MIP** | **46** | |

All tests use mocked dependencies — no external API calls. Fast, reliable, deterministic.

---

## 8. Migration Plan

### Phase 1 — Foundation (DONE)
- [x] MIP layer built alongside existing code
- [x] All 784 existing tests pass unchanged
- [x] 46 new MIP tests passing
- [x] No regression, no breaking changes

### Phase 2 — Internal Adoption (Next Sprint)
- [ ] `DecisionPipeline` switches from `HyperliquidCollector` → `MarketDataService.get_asset()`
- [ ] `ScoringEngine` receives pre-computed indicators from MIP instead of self-fetching
- [ ] API routes (`/market`, `/intelligence`, `/regime`) use MIP
- [ ] Remove `ScoringEngine`'s internal `HyperliquidCollector` dependency

### Phase 3 — Full Adoption (Sprint +2)
- [ ] `PaperExecutor` uses `MarketDataService.get_price()` instead of direct collector
- [ ] `ExecutionGuard` volatility check uses `IndicatorService`
- [ ] `WebSocket broadcast` uses MIP
- [ ] Remove all direct `HyperliquidCollector` instantiation outside `market_data/`

### Phase 4 — Deprecation (Future)
- [ ] `market_data/` becomes a thin wrapper over MIP
- [ ] All consumers migrate to `market.services`
- [ ] `market_data/` marked deprecated

---

## 9. Future-Readiness

The MIP architecture is designed to absorb future modules:

| Module | Enriched Field | Impact |
|---|---|---|
| **Scanner** | `Asset.indicators` + `Asset.features` | Uses pre-computed data, no duplicate work |
| **News Scanner** | `Asset.news` | Pure enrichment, no MIP changes |
| **Whale Tracker** | `Asset.whales` | Pure enrichment, no MIP changes |
| **AI Models** | `Asset.features` | Consumes existing features, adds predictions |
| **Terminal** | `MarketDataService.get_ohlcv()` | Uses existing API |

---

## 10. Files Created

```
market/
├── __init__.py
├── cache/
│   ├── __init__.py
│   └── manager.py          ← CacheManager (thread-safe, TTL, pattern invalidation)
├── context/
│   ├── __init__.py
│   └── service.py           ← ContextService (BTC, sessions, funding)
├── features/
│   ├── __init__.py
│   └── store.py             ← FeatureStore (categorical features)
├── indicators/
│   ├── __init__.py
│   └── service.py           ← IndicatorService (cached, once-computed indicators)
├── models/
│   ├── __init__.py
│   ├── asset.py             ← Asset + AssetMetadata (unified model)
│   └── ohlcv.py             ← OHLCVData (typed wrapper)
├── provider/
│   ├── __init__.py
│   ├── base.py              ← DataProvider protocol + OHLCVResult
│   └── hyperliquid.py       ← HyperliquidProvider (wraps existing collectors)
└── services/
    ├── __init__.py
    └── market_data.py       ← MarketDataService (single entry point)

tests/market/
├── __init__.py
├── test_asset_model.py
├── test_cache_manager.py
├── test_context_service.py
├── test_feature_store.py
├── test_hyperliquid_provider.py
├── test_indicator_service.py
└── test_market_data_service.py
```

**Total: 16 new files, 46 new tests, 0 regressions.**
