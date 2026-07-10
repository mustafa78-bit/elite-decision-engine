# SPRINT PLAN — Elite Decision Engine

> Detailed sprint-by-sprint plan from current state to Elite Platform Beta.
> Each sprint = 2 weeks. 22 sprints total = 44 weeks (~10 months).

---

## Quick Reference

| Sprint | Focus | Epic | SP | Team |
|--------|-------|------|----|------|
| 1–2 | Foundation Hardening | EPIC 1 | 8 | 1 BE |
| 3–5 | Execution Optimization | EPIC 2 | 13 | 1 BE |
| 6–7 | Production Readiness (part 1) | EPIC 11 | 8 | 1 BE + 1 FE |
| 8–10 | Elite Scanner | EPIC 3 | 21 | 1 BE + 1 FE |
| 11–13 | Market Intelligence | EPIC 4 | 21 | 1 BE + 1 FE |
| 14–17 | News Intelligence | EPIC 5 | 34 | 2 BE + 1 FE |
| 18–21 | Whale Intelligence | EPIC 6 | 34 | 2 BE + 1 FE |
| 22–24 | Portfolio Intelligence | EPIC 9 | 13 | 1 BE + 1 FE |
| 25–27 | Elite Terminal (part 1) | EPIC 8 | 20 | 2 FE |
| 28–30 | Elite Terminal (part 2) | EPIC 8 | 14 | 2 FE |
| 31–33 | Probability Engine (part 1) | EPIC 7 | 21 | 2 BE + 1 ML |
| 34–36 | Probability Engine (part 2) | EPIC 7 | 34 | 2 BE + 1 ML |
| 37–39 | AI Assistant (part 1) | EPIC 10 | 21 | 2 BE + 1 FE + 1 AI |
| 40–42 | AI Assistant (part 2) | EPIC 10 | 34 | 2 BE + 1 FE + 1 AI |
| 43–44 | Production Readiness (part 2) | EPIC 11 | 13 | 1 BE + 1 FE |
| 45–46 | Beta Launch | EPIC 12 | 13 | 1 BE + 1 FE |

---

## SPRINT 1: Foundation — Dependency Pinning & Build Setup

**Goal**: Secure the build pipeline and enable reproducible environments.

**Modules**: `requirements.txt`, `pyproject.toml`, `.dockerignore`, `.github/workflows/ci.yml`

**Files**:
- `requirements.txt` — pin all versions
- `pyproject.toml` — new file (project metadata, dev groups)
- `.dockerignore` — new file
- `.gitignore` — update

**Estimated Work**: 4 SP (BE)

**Tasks**:
1. Audit all Python dependencies and pin to current working versions
2. Create `pyproject.toml` with project metadata, dependency groups (dev/prod), and build system
3. Create `.dockerignore` with optimized exclusion patterns
4. Test `pip install -e .` works end-to-end

**Deliverables**:
- Version-pinned `requirements.txt`
- `pyproject.toml` with dev dependency group
- `.dockerignore` file
- CI still passes

**Definition of Done**:
- [ ] `pip install -r requirements.txt` produces identical virtualenv on two different machines
- [ ] `pip install -e .` installs the project in editable mode
- [ ] Docker build time reduced by 60%+
- [ ] CI passes

---

## SPRINT 2: Foundation — Database Migrations & Security

**Goal**: Add production-grade database migrations and fix security defaults.

**Modules**: `database.py`, `docker-compose.yml`, `docker-compose.prod.yml`

**Files**:
- `alembic/` — new directory
- `alembic.ini` — new file
- `database.py` — add migration support
- `docker-compose.yml` — remove default JWT_SECRET
- `.env.example` — update

**Estimated Work**: 4 SP (BE)

**Tasks**:
1. Set up Alembic with initial migration for all 7 SQLAlchemy models
2. Move JWT_SECRET default from docker-compose.yml to mandatory env var
3. Remove committed log files and test databases from git tracking
4. Configure Dependabot in GitHub

**Deliverables**:
- `alembic/versions/0001_initial.py` migration
- Updated docker-compose files with mandatory env vars
- Clean git status (no log files, no .db files)
- `.github/dependabot.yml`

**Definition of Done**:
- [ ] `alembic upgrade head` creates all 7 tables in empty PostgreSQL
- [ ] `alembic downgrade -1` rolls back cleanly
- [ ] Container fails to start if JWT_SECRET is not set
- [ ] Dependabot alerts configured for Python and npm

---

## SPRINT 3: Execution — Async Main Loop

**Goal**: Replace the blocking `while True` loop with an async event loop.

**Modules**: `core/engine.py`, `app.py`

**Files**:
- `core/engine.py` — full rewrite of `DecisionEngine.run()`
- `app.py` — update entry point for async
- `core/__init__.py` — update exports

**Estimated Work**: 5 SP (BE)

**Tasks**:
1. Refactor `DecisionEngine` to use `asyncio` event loop
2. Replace `time.sleep(CHECK_INTERVAL)` with `asyncio.sleep()`
3. Add configurable concurrency for signal processing
4. Ensure graceful shutdown via signal handlers
5. Update `app.py` to use `asyncio.run()` (or `uvicorn` for API mode)

**Deliverables**:
- Async `DecisionEngine` with signal handler for graceful shutdown
- Concurrent signal processing (configurable pool size)

**Definition of Done**:
- [ ] Engine starts, processes signals, and shuts down cleanly
- [ ] KeyboardInterrupt (Ctrl+C) works gracefully
- [ ] Concurrent processing handles 10 signals in parallel
- [ ] All existing tests pass

---

## SPRINT 4: Execution — Caching & Data Optimization

**Goal**: Eliminate duplicate data fetches and add caching to reduce external API calls.

**Modules**: `execution/pipeline.py`, `scoring/scoring_engine.py`, `market_data/`

**Files**:
- `execution/pipeline.py` — pass market data to scoring engine
- `scoring/scoring_engine.py` — accept pre-fetched data
- `market_data/cache/` — new caching module
- `api/cache.py` — update for Redis cache integration

**Estimated Work**: 5 SP (BE)

**Tasks**:
1. Implement in-memory TTL cache (or Redis) for OHLCV data
2. Refactor `ScoringEngine.score()` to accept optional pre-computed market data
3. Update `DecisionPipeline.evaluate()` to compute data once and pass to scoring
4. Add cache invalidation strategy (time-based + explicit)
5. Move static `_is_empty_market_data()` to shared utility

**Deliverables**:
- Shared TTL cache for market data
- Single OHLCV fetch per pipeline evaluation
- Shared utility module for common functions

**Definition of Done**:
- [ ] Pipeline + Scoring share one data fetch (verified via logging)
- [ ] Redis cache hits reduce external API calls by 80%+ during normal operation
- [ ] Cache TTL is configurable
- [ ] No duplicate `_is_empty_market_data()` in codebase

---

## SPRINT 5: Execution — Performance & Scalability

**Goal**: Add pagination, rate limiting, and faster WebSocket broadcasts.

**Modules**: `api/routes/*`, `api/websocket/`, `api/main.py`

**Files**:
- `api/main.py` — increase broadcast frequency
- `api/routes/signals.py` — add pagination
- `api/routes/trades.py` — add pagination
- `api/routes/notifications.py` — add pagination
- `api/middleware.py` — add rate limiting

**Estimated Work**: 3 SP (BE)

**Tasks**:
1. Add page/per_page query params to all list endpoints
2. Add rate limiting middleware (token bucket algorithm)
3. Increase WebSocket broadcast to 5s interval
4. Add API response time tracking metric

**Deliverables**:
- Paginated list endpoints
- Rate-limited API (configurable limits)
- 5-second WebSocket market broadcasts

**Definition of Done**:
- [ ] `GET /v1/signals?page=2&per_page=25` returns paginated results with total count
- [ ] 429 Too Many Requests returned when rate limit exceeded
- [ ] WebSocket market updates arrive every 5 seconds (±1s)
- [ ] All existing tests pass

---

## SPRINT 6: Production Readiness — Testing (Part 1)

**Goal**: Add critical integration tests and backup script.

**Modules**: `tests/`, `scripts/`

**Files**:
- `tests/test_e2e_pipeline.py` — new integration test
- `scripts/backup.sh` — new backup script
- `.github/workflows/ci.yml` — add integration test step

**Estimated Work**: 5 SP (BE + FE)

**Tasks**:
1. Write end-to-end integration test: Signal → Pipeline → ExecutionLoop → TradeEngine → PaperExecutor
2. Create `scripts/backup.sh` for PostgreSQL to S3 backup
3. Add backup script execution to production docker-compose health check
4. Add CI step for integration tests (requires Postgres service)

**Deliverables**:
- E2E integration test covering full pipeline
- Production backup script
- CI with integration test job

**Definition of Done**:
- [ ] E2E test creates signal, runs pipeline, creates trade, verifies paper execution
- [ ] Backup script creates encrypted S3 backup and cleans old backups
- [ ] CI runs integration tests on push to main

---

## SPRINT 7: Production Readiness — Testing (Part 2)

**Goal**: Add API contract tests and frontend E2E tests.

**Modules**: `tests/`, `frontend/src/test/`

**Files**:
- `tests/test_api_contracts.py` — new API contract tests
- `frontend/e2e/` — new Playwright test directory
- `.github/workflows/ci.yml` — add E2E test job

**Estimated Work**: 3 SP (BE + FE)

**Tasks**:
1. Write contract tests for all API routes (status codes, response schemas)
2. Set up Playwright for frontend E2E testing
3. Write E2E tests for dashboard page and trade flow
4. Add E2E job to CI

**Deliverables**:
- API contract test suite (30+ route tests)
- Frontend E2E tests (3+ critical flows)
- CI pipeline runs E2E tests

**Definition of Done**:
- [ ] All 31 API routes have contract tests
- [ ] Frontend dashboard renders in Playwright test
- [ ] CI pipeline completes in <15 minutes

---

## SPRINT 8: Elite Scanner (Part 1)

**Goal**: Build the scanning engine architecture and symbol universe manager.

**Modules**: `scanner/` (new module)

**Files**:
- `scanner/__init__.py`
- `scanner/engine.py` — scan orchestrator
- `scanner/universe.py` — symbol universe manager
- `scanner/models.py` — scan result models

**Estimated Work**: 5 SP (BE)

**Tasks**:
1. Design scanner module structure with interfaces for scan strategies
2. Build symbol universe manager (tiered: Core 20 / Alt 50 / All)
3. Implement scan results data model (extends Signal model)
4. Build scan scheduler with configurable intervals

**Deliverables**:
- Scanner module with DI support
- Symbol universe manager with persistence
- Scan scheduler (configurable via API)

**Definition of Done**:
- [ ] Universe manager returns symbol list filtered by tier
- [ ] Scanner can be configured for any timeframe
- [ ] Scan tasks are scheduled and executed

---

## SPRINT 9: Elite Scanner (Part 2)

**Goal**: Implement divergence detection and pattern recognition.

**Modules**: `scanner/`

**Files**:
- `scanner/divergence.py` — RSI/MACD divergence detector
- `scanner/patterns.py` — candlestick pattern recognition
- `scanner/support_resistance.py` — S/R level detection

**Estimated Work**: 8 SP (BE)

**Tasks**:
1. Implement RSI divergence detector (regular, hidden, both directions)
2. Implement MACD crossover detection
3. Implement candlestick pattern recognition (engulfing, doji, hammer, pin bar)
4. Implement support/resistance level detection
5. Add pattern confidence scoring

**Deliverables**:
- Divergence detection across all configured symbols
- Candlestick pattern library (10+ patterns)
- S/R level detection with confidence scores

**Definition of Done**:
- [ ] Scanner detects RSI divergence on all core universe symbols
- [ ] Scanner recognizes 10+ candlestick patterns
- [ ] Scan results include confidence score for each pattern
- [ ] False positive rate <30% (validated on historical data)

---

## SPRINT 10: Elite Scanner (Part 3)

**Goal**: Scanner integration with pipeline and frontend.

**Modules**: `scanner/`, `execution/pipeline.py`, `frontend/src/pages/`

**Files**:
- `scanner/service.py` — scanner service
- `api/routes/scanner.py` — scanner API endpoints
- `frontend/src/pages/Scanner.tsx` — scanner page
- `frontend/src/api/scanner.ts` — scanner API client

**Estimated Work**: 8 SP (BE + FE)

**Tasks**:
1. Integrate scanner results with `Signal` model and `ExecutionLoop`
2. Build scanner API endpoints (`GET /v1/scanner/results`, `GET /v1/scanner/symbols`, `POST /v1/scanner/scan`)
3. Build scanner frontend page with signal feed
4. Add real-time updates via WebSocket

**Deliverables**:
- Scanner feeds signals into existing pipeline
- Scanner API endpoints
- Scanner frontend page with signal feed

**Definition of Done**:
- [ ] Scan results persist as `Signal` records in DB
- [ ] Scanner signals flow through pipeline → execution → paper trade
- [ ] Scanner page shows live results from all scan strategies
- [ ] Results filterable by symbol, pattern type, confidence

---

## SPRINT 11: Market Intelligence (Part 1)

**Goal**: Upgrade BTC health with on-chain metrics and add correlation engine.

**Modules**: `market_data/`, `scoring/`

**Files**:
- `market_data/btc_health.py` — add on-chain metrics
- `market_data/correlation.py` — new correlation engine
- `market_data/sector.py` — new sector rotation detector

**Estimated Work**: 5 SP (BE)

**Tasks**:
1. Integrate on-chain data provider (Glassnode or similar)
2. Add MVRV Z-Score, SOPR, NUPL metrics to BTCHealth
3. Build market correlation engine (Pearson/Spearman)
4. Implement sector classification for top 100 tokens

**Deliverables**:
- Enhanced BTC health dashboard with on-chain metrics
- Correlation matrix engine
- Sector classification system

**Definition of Done**:
- [ ] BTC health page shows MVRV, SOPR, NUPL charts
- [ ] Correlation matrix available for 20+ trading pairs
- [ ] Sector classification covers 100+ tokens (L1, L2, DeFi, Gaming, Meme, etc.)

---

## SPRINT 12: Market Intelligence (Part 2)

**Goal**: Build liquidity heatmap and funding rate intelligence.

**Modules**: `market_data/`, `exchange/`

**Files**:
- `market_data/liquidity.py` — liquidity heatmap
- `market_data/funding/collector.py` — upgrade funding collector
- `market_data/oi.py` — open interest analysis

**Estimated Work**: 8 SP (BE)

**Tasks**:
1. Build aggregated liquidity heatmap from order book data
2. Upgrade funding rate collector with multi-exchange aggregation
3. Implement open interest delta detection (OI change %)
4. Add liquidity and OI scoring to pipeline

**Deliverables**:
- Liquidity heatmap per symbol/exchange
- Multi-exchange funding rate dashboard
- Open interest delta alerts

**Definition of Done**:
- [ ] Liquidity heatmap shows bid/ask depth across 3+ exchanges
- [ ] Funding rates aggregated and displayed per symbol
- [ ] OI delta > 10% triggers notification
- [ ] Liquidity and OI scores feed into scoring engine

---

## SPRINT 13: Market Intelligence (Part 3)

**Goal**: Upgrade regime engine and build Market Intelligence frontend.

**Modules**: `scoring/`, `frontend/src/pages/`

**Files**:
- `scoring/regime_ai.py` — add probability scores
- `api/routes/market_intelligence.py` — new endpoints
- `frontend/src/pages/MarketIntelligence.tsx` — upgrade page
- `frontend/src/api/market_intelligence.ts`

**Estimated Work**: 8 SP (BE + FE)

**Tasks**:
1. Upgrade RegimeAI with regime probability scores (not just classifications)
2. Add regime transition detection (trend → range, etc.)
3. Build Market Intelligence API endpoints
4. Upgrade Market Intelligence frontend with heatmaps, charts, metrics
5. Add WebSocket channel for market intelligence data

**Deliverables**:
- RegimeAI with probability scores
- Market Intelligence API
- Upgraded Market Intelligence dashboard

**Definition of Done**:
- [ ] Regime detection returns probability distribution across regimes
- [ ] Market Intelligence page shows heatmap, correlation matrix, sector rotation
- [ ] Funding rate and OI charts render correctly
- [ ] WebSocket updates market intelligence data in real-time

---

## SPRINT 14: News Intelligence (Part 1)

**Goal**: Build news ingestion pipeline.

**Modules**: `news/` (new module)

**Files**:
- `news/__init__.py`
- `news/ingestor.py` — news ingestion pipeline
- `news/sources.py` — news source adapters
- `news/models.py` — news article data model

**Estimated Work**: 5 SP (BE)

**Tasks**:
1. Design news module architecture
2. Integrate NewsAPI and CryptoCompare
3. Build news ingestion pipeline (fetch → normalize → classify → store)
4. Implement article deduplication

**Deliverables**:
- News ingestion pipeline fetching from 2+ sources
- Normalized news article storage in DB
- Deduplication system

**Definition of Done**:
- [ ] News articles ingested from NewsAPI and CryptoCompare
- [ ] Articles normalized to common schema and stored in DB
- [ ] Duplicate articles are detected and rejected
- [ ] Ingestion rate: 1000+ articles/hour

---

## SPRINT 15: News Intelligence (Part 2)

**Goal**: Build NLP sentiment analysis and news classification.

**Modules**: `news/`

**Files**:
- `news/sentiment.py` — NLP sentiment analyzer
- `news/classifier.py` — news classifier
- `news/impact.py` — market impact analyzer

**Estimated Work**: 10 SP (BE)

**Tasks**:
1. Implement finBERT-based sentiment analysis for crypto news
2. Build news classification system (by asset, category, impact level)
3. Implement source quality scoring system
4. Build news-to-signal bridge

**Deliverables**:
- NLP sentiment analysis pipeline
- News classification system
- Source reputation scoring
- Sentiment → Signal bridge

**Definition of Done**:
- [ ] Sentiment score per article (positive/negative/neutral + confidence)
- [ ] Articles classified by asset (BTC, ETH, SOL, etc.)
- [ ] Source quality score tracked and applied as weight
- [ ] High-impact news events generate signals in the system

---

## SPRINT 16: News Intelligence (Part 3)

**Goal**: News API and frontend.

**Modules**: `api/routes/`, `frontend/src/pages/`

**Files**:
- `api/routes/news.py` — news API endpoints
- `frontend/src/pages/NewsIntelligence.tsx` — news page
- `frontend/src/api/news.ts` — news API client

**Estimated Work**: 10 SP (BE + FE)

**Tasks**:
1. Build news API endpoints (list, search, sentiment, sources)
2. Build News Intelligence frontend (news feed, sentiment charts, impact analysis)
3. Add real-time news alerts via WebSocket
4. Add historical news backtesting capability

**Deliverables**:
- News API with full CRUD + search
- News Intelligence frontend page
- News alerting system
- Backtest historical news impact

**Definition of Done**:
- [ ] News feed renders with sentiment indicators
- [ ] Sentiment chart shows bullish/bearish balance over time
- [ ] News alerts trigger when impact score exceeds threshold
- [ ] Backtest shows correlation between news sentiment and price movement

---

## SPRINT 17: News Intelligence — Polish & Verification

**Goal**: Validate news intelligence accuracy and optimize.

**Modules**: `news/`, `tests/`

**Files**:
- `tests/test_news_intelligence.py`
- `news/config.py` — news module configuration

**Estimated Work**: 9 SP (BE + FE)

**Tasks**:
1. Validate sentiment accuracy against labeled dataset (target: >75% accuracy)
2. Tune impact scoring thresholds
3. Optimize ingestion pipeline performance
4. Write comprehensive test suite for news module

**Deliverables**:
- Verified sentiment accuracy
- Tested and tuned impact scoring
- News module test suite

**Definition of Done**:
- [ ] Sentiment accuracy ≥75% on validation dataset
- [ ] All news components have unit tests
- [ ] Integration test covers news → signal → pipeline flow
- [ ] Ingestion handles 5000+ articles/hour without degradation

---

## SPRINT 18: Whale Intelligence (Part 1)

**Goal**: Build whale wallet tracking system.

**Modules**: `whale/` (new module)

**Files**:
- `whale/__init__.py`
- `whale/tracker.py` — wallet tracker
- `whale/config.py` — whale module config
- `whale/models.py` — whale data models

**Estimated Work**: 8 SP (BE)

**Tasks**:
1. Design whale intelligence module architecture
2. Integrate on-chain data provider (Etherscan API for EVM chains)
3. Build whale wallet database (tracked wallets with labels)
4. Implement large transaction detection

**Deliverables**:
- Whale wallet tracker
- Transaction detection pipeline
- Wallet database with labeling

**Definition of Done**:
- [ ] Tracks 1000+ labeled whale wallets
- [ ] Detects transactions >$100K in real-time
- [ ] Wallet labels include: exchange, defi, foundation, known whale

---

## SPRINT 19: Whale Intelligence (Part 2)

**Goal**: Build exchange flow tracking and accumulation/distribution detection.

**Modules**: `whale/`

**Files**:
- `whale/exchange_flow.py` — exchange flow tracker
- `whale/accumulation.py` — accumulation/distribution detection
- `whale/alerting.py` — whale alert system

**Estimated Work**: 10 SP (BE)

**Tasks**:
1. Build exchange flow tracking (inflows/outflows by exchange)
2. Implement accumulation/distribution detection algorithm
3. Build whale alerting system
4. Create whale-to-signal bridge

**Deliverables**:
- Exchange flow tracking dashboard
- Accumulation/distribution signals
- Whale alert system integrated with notifications

**Definition of Done**:
- [ ] Exchange flow tracked for 10+ exchanges
- [ ] Accumulation pattern detected (sustained inflows to cold wallets)
- [ ] Distribution pattern detected (sustained outflows to exchanges)
- [ ] Whale signals generated and feed into pipeline

---

## SPRINT 20: Whale Intelligence (Part 3)

**Goal**: Whale API and frontend.

**Modules**: `api/routes/`, `frontend/src/pages/`

**Files**:
- `api/routes/whale.py` — whale API endpoints
- `frontend/src/pages/WhaleDashboard.tsx` — upgrade from placeholder
- `frontend/src/api/whale.ts`

**Estimated Work**: 8 SP (BE + FE)

**Tasks**:
1. Build Whale Intelligence API endpoints
2. Build Whale Dashboard frontend (whale movements, flow charts, alerts)
3. Implement whale correlation with price movement
4. Add real-time whale alerts via WebSocket

**Deliverables**:
- Whale API
- Whale Dashboard (replaces placeholder page)
- Price correlation analysis

**Definition of Done**:
- [ ] Whale page shows live whale movements with wallet labels
- [ ] Exchange flow chart shows aggregate inflows/outflows
- [ ] Whale alerts appear in notification center
- [ ] Price correlation chart shows whale activity vs price

---

## SPRINT 21: Whale Intelligence (Part 4)

**Goal**: Multi-chain support and polish.

**Modules**: `whale/`

**Files**:
- `whale/chains/` — multi-chain adapters
- `tests/test_whale_intelligence.py`

**Estimated Work**: 8 SP (BE + FE)

**Tasks**:
1. Add Solana support via Solana RPC
2. Add Arbitrum and BSC support
3. Unify multi-chain wallet tracking
4. Write comprehensive test suite

**Deliverables**:
- Multi-chain whale tracking (ETH, SOL, ARB, BSC)
- Unified wallet view across chains
- Whale test suite

**Definition of Done**:
- [ ] Whale tracking works on 4+ chains
- [ ] Wallet view shows holdings across all tracked chains
- [ ] All whale components have unit tests
- [ ] Integration test covers whale → signal flow

---

## SPRINT 22: Portfolio Intelligence (Part 1)

**Goal**: Build portfolio risk analytics.

**Modules**: `services/portfolio_service.py`, `risk/`

**Files**:
- `services/portfolio_service.py` — upgrade with risk analytics
- `portfolio_engine.py` — add risk metrics
- `risk/models.py` — add VaR models

**Estimated Work**: 5 SP (BE)

**Tasks**:
1. Implement VaR calculation (95%, 99% confidence)
2. Implement CVaR (Expected Shortfall)
3. Calculate Sharpe, Sortino, Calmar ratios
4. Build drawdown analysis with recovery tracking

**Deliverables**:
- Portfolio risk analytics API
- Risk metrics integrated into portfolio service

**Definition of Done**:
- [ ] Portfolio dashboard shows VaR 95%, VaR 99%, CVaR
- [ ] Sharpe, Sortino, Calmar ratios calculated and displayed
- [ ] Drawdown chart with recovery timeline
- [ ] All metrics update in real-time via WebSocket

---

## SPRINT 23: Portfolio Intelligence (Part 2)

**Goal**: Build portfolio optimization and correlation analysis.

**Modules**: `services/`, `frontend/src/pages/`

**Files**:
- `services/portfolio_service.py` — add optimization
- `api/routes/portfolio_detail.py` — add analysis endpoints
- `frontend/src/pages/PortfolioDetailPage.tsx` — upgrade visualization

**Estimated Work**: 5 SP (BE + FE)

**Tasks**:
1. Implement mean-variance optimization (Efficient Frontier)
2. Implement risk parity optimization
3. Build correlation analysis across portfolio positions
4. Add portfolio stress testing (what-if scenarios)

**Deliverables**:
- Portfolio optimization API
- Efficient Frontier visualization
- Correlation matrix for portfolio
- What-if scenario engine

**Definition of Done**:
- [ ] Efficient Frontier chart shows optimal portfolios
- [ ] Risk parity weights calculated
- [ ] Stress test: "What if BTC drops 20%?" shows impact on portfolio

---

## SPRINT 24: Portfolio Intelligence (Part 3)

**Goal**: Performance attribution and frontend upgrade.

**Modules**: `services/`, `frontend/src/pages/`

**Files**:
- `services/portfolio_service.py` — performance attribution
- `frontend/src/pages/Portfolio.tsx` — upgrade
- `frontend/src/stores/portfolio-store.ts` — new store

**Estimated Work**: 3 SP (BE + FE)

**Tasks**:
1. Implement performance attribution (allocation, selection, timing effects)
2. Build portfolio rebalancing recommendations
3. Upgrade Portfolio frontend with advanced visualizations

**Deliverables**:
- Performance attribution system
- Rebalancing recommendation engine
- Upgraded Portfolio frontend

**Definition of Done**:
- [ ] Performance attribution shows source of returns
- [ ] Rebalancing recommendations with cost estimates
- [ ] Portfolio frontend shows all risk metrics, optimization, attribution

---

## SPRINT 25: Elite Terminal (Part 1)

**Goal**: Upgrade chart engine with multi-timeframe, multi-symbol support.

**Modules**: `frontend/src/components/trading/`

**Files**:
- `frontend/src/components/trading/chart-panel.tsx` — upgrade
- `frontend/src/components/trading/multi-chart-layout.tsx` — upgrade
- `frontend/src/components/trading/chart-toolbar.tsx` — upgrade
- `frontend/src/components/trading/chart-markers.tsx` — upgrade

**Estimated Work**: 10 SP (FE)

**Tasks**:
1. Upgrade chart panel to support 6 timeframes (1m → 1d)
2. Add multi-symbol support (compare up to 4 symbols)
3. Implement chart drawing tools (trendlines, fib retracement, horizontal lines)
4. Add trade markers on chart (entry, TP, SL)

**Deliverables**:
- Multi-timeframe chart component
- Multi-symbol comparison chart
- Drawing tools library
- Trade markers on chart

**Definition of Done**:
- [ ] Chart switches between 6 timeframes without reload
- [ ] Up to 4 symbols can be overlaid
- [ ] Drawing tools: trendline, fib, horizontal, vertical lines
- [ ] Open trades shown as markers with entry/TP/SL levels

---

## SPRINT 26: Elite Terminal (Part 2)

**Goal**: Implement advanced order types and professional workspace.

**Modules**: `frontend/src/components/trading/`

**Files**:
- `frontend/src/components/trading/oco-panel.tsx` — OCO order panel
- `frontend/src/components/trading/order-panel.tsx` — upgrade
- `frontend/src/components/workspace/multi-panel-layout.tsx` — upgrade
- `frontend/src/components/workspace/dockable-widget.tsx` — upgrade

**Estimated Work**: 10 SP (FE)

**Tasks**:
1. Implement OCO (One-Cancels-Other) order panel in UI
2. Add trailing stop order input
3. Build professional workspace with detachable panels
4. Implement layout presets for different trading styles

**Deliverables**:
- OCO and trailing stop order UI
- Professional workspace with undocked panels
- Layout preset system (Day Trader, Swing Trader, Analyst)

**Definition of Done**:
- [ ] OCO panel allows setting limit + stop simultaneously
- [ ] Trailing stop shows current activation price
- [ ] Panels can be undocked into separate browser windows
- [ ] 3 layout presets available with one-click switching

---

## SPRINT 27: Elite Terminal (Part 3)

**Goal**: Trading analytics and alert system.

**Modules**: `frontend/src/components/trading/`, `api/routes/`

**Files**:
- `frontend/src/components/trading/execution-analytics.tsx` — execution analytics
- `frontend/src/components/trading/post-trade-analysis.tsx` — post-trade analysis
- `frontend/src/components/trading/trade-journal.tsx` — trade journal upgrade
- `api/routes/alerts.py` — alert endpoints (new)

**Estimated Work**: 14 SP (BE + FE)

**Tasks**:
1. Build execution analytics (slippage, fill rate, latency metrics)
2. Implement post-trade analysis (PnL attribution, exit timing)
3. Upgrade trade journal with screenshots and grading
4. Build alert system (API + WebSocket + frontend)

**Deliverables**:
- Execution analytics dashboard
- Post-trade analysis view
- Upgraded trade journal
- Full alert system

**Definition of Done**:
- [ ] Execution analytics shows slippage % per trade
- [ ] Post-trade analysis shows optimal exit vs actual exit
- [ ] Trade journal supports screenshots, tags, and grades
- [ ] Price alerts trigger at configured levels via WebSocket

---

## SPRINT 28–30: Probability Engine (Spans 3 sprints)

**Goal**: Build ML-powered probability prediction for trade outcomes.

**Modules**: `probability/` (new module), `scoring/confidence_engine.py`

**Files**: (See ROADMAP EPIC 7 for full file list)

**Estimated Work**: 55 SP (BE + ML)

**Tasks**: (See ROADMAP EPIC 7 for full task list)

**Sprint 28**: Data pipeline, feature engineering, baseline model (Bayesian)
**Sprint 29**: ML model training pipeline, model serving, Monte Carlo simulation
**Sprint 30**: Integration with ConfidenceEngine, frontend, monitoring

**Deliverables**:
- Probability prediction model with 60%+ accuracy
- Monte Carlo simulation for trade outcome distribution
- Probability-aware trade approval system

---

## SPRINT 31–34: AI Assistant (Spans 4 sprints)

**Goal**: Build natural language AI assistant for trading.

**Modules**: `assistant/` (new module)

**Files**: (See ROADMAP EPIC 10 for full file list)

**Estimated Work**: 55 SP (BE + FE + AI)

**Tasks**: (See ROADMAP EPIC 10 for full task list)

**Sprint 31**: Architecture, LLM integration, prompt framework
**Sprint 32**: Trade explanation engine, market Q&A system
**Sprint 33**: Portfolio analysis, risk explanations, signal generation
**Sprint 34**: Chat frontend, RAG system, cost tracking

---

## SPRINT 35–36: Production Readiness (Part 2)

**Goal**: Final testing, documentation, and operations readiness.

**Modules**: All

**Files**:
- `tests/test_load.py` — load testing
- `docs/` — documentation files
- `scripts/runbooks/` — operations runbooks
- `.githooks/` — git hooks

**Estimated Work**: 13 SP (BE + FE)

**Tasks**:
1. Load testing with locust/k6 (target: 1000 req/s)
2. Frontend E2E tests for all critical flows
3. Create operations runbooks
4. Add pre-commit hooks
5. Finalize API documentation
6. Performance profiling and optimization pass

**Deliverables**:
- Load test report
- Complete E2E test suite
- Operations runbook
- Pre-commit hooks
- Complete API docs

---

## SPRINT 37–38: Beta Launch

**Goal**: Final integration, security audit, and Beta launch.

**Modules**: All

**Files**:
- Security audit report
- Beta onboarding flow
- Monitoring dashboards

**Estimated Work**: 13 SP (BE + FE)

**Tasks**:
1. Full system integration testing
2. Security audit (penetration testing, dependency scan)
3. Performance optimization
4. UX polish pass
5. Create Beta onboarding flow
6. Set up Grafana monitoring dashboards
7. Beta launch deployment

**Deliverables**:
- Security audit passed
- Beta platform deployed
- Monitoring dashboards active
- Onboarding flow ready

---

*End of SPRINT_PLAN.md*
