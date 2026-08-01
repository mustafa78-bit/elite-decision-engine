# ROADMAP — Elite Decision Engine

> Complete development roadmap from current state to Elite Platform Beta.
> All estimates in story points (1 SP = 1 ideal dev-day).

---

## Current State Assessment

```
CURRENT: Paper Trading Engine with Full Frontend Dashboard
         ├── Execution Pipeline ✅
         ├── Paper Executor (TP/SL) ✅
         ├── Scoring Engine (5-component) ✅
         ├── Market Intelligence (basic) ✅
         ├── REST API (31 routes) ✅
         ├── WebSocket (6 rooms) ✅
         ├── Frontend (33 pages) ✅
         ├── Docker/CI-CD ✅
         └── Exchange Adapters (HL, Binance) ✅

BETA GOAL: Enterprise AI Decision Intelligence Platform
           ├── Elite Scanner           ❌
           ├── Market Intelligence     ⚠️ (partial)
           ├── News Intelligence       ❌
           ├── Whale Intelligence      ❌
           ├── Probability Engine      ❌
           ├── Elite Terminal          ⚠️ (partial)
           ├── Portfolio Intelligence  ⚠️ (partial)
           └── AI Assistant            ❌
```

---

## EPIC 1: Foundation Hardening

**Purpose**: Address all technical debt, security issues, and infrastructure gaps before building new features. This foundation is required for all future work.

**Architecture Impact**: Low architectural change, high quality-of-life improvement. Touches all layers (build, deploy, database, API).

**Estimated Complexity**: XXS (8 SP)

**Dependencies**: None — can start immediately.

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| F-01 | Pin all Python dependency versions in `requirements.txt` | 1 SP | CRITICAL |
| F-02 | Create `pyproject.toml` with project metadata + dev/prod dep grouping | 1 SP | HIGH |
| F-03 | Create `.dockerignore` to exclude .git, .venv, node_modules, __pycache__ | 1 SP | HIGH |
| F-04 | Remove committed log files (engine.log, trade.log, error.log) + add to gitignore | 0.5 SP | MEDIUM |
| F-05 | Remove committed test databases (test_elite.db) | 0.5 SP | MEDIUM |
| F-06 | Add database migration system (Alembic) — initial migration for all 7 tables | 2 SP | CRITICAL |
| F-07 | Move JWT_SECRET default from docker-compose.yml to mandatory env var | 0.5 SP | CRITICAL |
| F-08 | Add API versioning prefix to all routes (e.g., `/v1/signals`) | 1.5 SP | MEDIUM |
| F-09 | Configure Dependabot for automated dependency security scanning | 0.5 SP | MEDIUM |
| F-10 | Add `.env` file validation in `config.py` with pydantic-settings | 1 SP | MEDIUM |

### Risks
- Alembic migration must handle existing data without loss.
- API versioning will require frontend client updates in the same PR.

### Acceptance Criteria
- [ ] `pip install -r requirements.txt` produces identical environments across machines.
- [ ] `pip install -e .` works via `pyproject.toml`.
- [ ] Docker builds are 2x faster with `.dockerignore`.
- [ ] No log files or `.db` files in git tracking.
- [ ] `alembic history` shows initial migration.
- [ ] All API routes accessible via `/v1/*`.
- [ ] Dependabot PRs created for vulnerable dependencies.

---

## EPIC 2: Execution Engine Optimization

**Purpose**: Fix the blocking main loop, add caching, and make the execution engine production-ready and scalable.

**Architecture Impact**: Medium. Changes `core/engine.py` and adds async patterns. Introduces a caching layer.

**Estimated Complexity**: S (13 SP)

**Dependencies**: EPIC 1 (Foundation Hardening)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| E-01 | Refactor `DecisionEngine.run()` from blocking `while True` to async `asyncio` loop | 3 SP | HIGH |
| E-02 | Add market data caching layer (Redis or in-memory TTL cache) | 2 SP | HIGH |
| E-03 | Eliminate duplicate OHLCV fetch in pipeline + scoring by passing data through | 1 SP | HIGH |
| E-04 | Add concurrent signal processing in `ExecutionLoop.run_once()` | 2 SP | MEDIUM |
| E-05 | Increase WebSocket broadcast interval to 5s (from 30s) with rate limiting | 1 SP | MEDIUM |
| E-06 | Add database session scope per request (request-scoped sessions) | 2 SP | MEDIUM |
| E-07 | Add API response pagination for signals, trades, notifications endpoints | 2 SP | HIGH |
| E-08 | Add API rate limiting middleware (token bucket or sliding window) | 1 SP | MEDIUM |

### Risks
- Async refactor may introduce race conditions in WebSocket broadcasting.
- Caching market data may lead to stale signal evaluation.

### Acceptance Criteria
- [ ] `DecisionEngine` runs async with configurable concurrency.
- [ ] Pipeline + Scoring share one OHLCV fetch per signal evaluation.
- [ ] Redis cache reduces Hyperliquid API calls by 80%+.
- [ ] WebSocket broadcasts market state every 5 seconds.
- [ ] All list endpoints support `?page=1&per_page=50` pagination.
- [ ] `/v1/signals` returns 429 when rate limit exceeded.

---

## EPIC 3: Elite Scanner

**Purpose**: Build the signal scanning engine that continuously monitors markets and generates high-quality trading signals.

**Architecture Impact**: Medium. New module `scanner/` with its own data pipeline. Integrates with existing `ExecutionLoop`.

**Estimated Complexity**: M (21 SP)

**Dependencies**: EPIC 2 (Execution Engine Optimization)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| S-01 | Design `Scanner` module architecture: multi-timeframe scanner, configurable symbol universe | 1 SP | HIGH |
| S-02 | Implement symbol universe manager (configurable, persisted, tiered: Core/Alt/All) | 2 SP | HIGH |
| S-03 | Build multi-timeframe scanner (1m, 5m, 15m, 1h, 4h, 1d) | 4 SP | HIGH |
| S-04 | Implement divergence detector (RSI/MACD bullish/bearish divergence scanning) | 3 SP | HIGH |
| S-05 | Implement pattern recognition (support/resistance, trendline breaks, candlestick patterns) | 3 SP | MEDIUM |
| S-06 | Add scanner scheduling system (configurable scan intervals per timeframe) | 2 SP | HIGH |
| S-07 | Integrate scanner output with existing `Signal` model and `ExecutionLoop` | 2 SP | HIGH |
| S-08 | Add scanner API endpoints (`/v1/scanner/results`, `/v1/scanner/symbols`) | 2 SP | MEDIUM |
| S-09 | Build Scanner frontend page with live results table | 2 SP | MEDIUM |

### Risks
- Scanning 100+ symbols across 6 timeframes = 600 data fetches per cycle. Must use caching.
- Pattern recognition may produce false positives without proper validation.

### Acceptance Criteria
- [ ] Scanner scans configured symbol universe (default: top 20 by volume).
- [ ] Detects RSI divergence, MACD crossover, candlestick patterns.
- [ ] Results persisted as `Signal` records in database.
- [ ] Scanner frontend shows live results with filtering.
- [ ] Scanner respects rate limits and caches aggressively.

---

## EPIC 4: Market Intelligence Platform

**Purpose**: Upgrade market intelligence from basic BTC health + regime to a full market analysis platform with multiple data dimensions.

**Architecture Impact**: Medium. Extends `market_data/` and `scoring/` modules. Adds new API and frontend pages.

**Estimated Complexity**: M (21 SP)

**Dependencies**: EPIC 1 (Foundation Hardening)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| MI-01 | Upgrade `BTCHealth` with on-chain metrics (MVRV, SOPR, NUPL) | 3 SP | HIGH |
| MI-02 | Build market dominance and correlation analysis engine | 2 SP | HIGH |
| MI-03 | Add sector rotation detection (L1, L2, DeFi, Gaming sectors) | 3 SP | MEDIUM |
| MI-04 | Implement liquidity heatmap (order book depth across exchanges) | 2 SP | HIGH |
| MI-05 | Build funding rate intelligence (aggregated across exchanges) | 2 SP | MEDIUM |
| MI-06 | Implement open interest analysis with delta change detection | 2 SP | HIGH |
| MI-07 | Add market regime upgrade with regime probability scores | 2 SP | HIGH |
| MI-08 | Build Market Intelligence API endpoints | 2 SP | MEDIUM |
| MI-09 | Upgrade Market Intelligence frontend with heatmaps, charts, and metrics | 3 SP | MEDIUM |

### Risks
- On-chain metrics require third-party API integration (Glassnode, CoinMetrics, etc.).
- Data aggregation across exchanges requires additional exchange connectors.

### Acceptance Criteria
- [ ] BTC health dashboard shows on-chain metrics.
- [ ] Market correlation matrix available with top 20 assets.
- [ ] Sector rotation detection identifies capital flows.
- [ ] Funding rate dashboard shows aggregated rates.
- [ ] Open interest analysis shows delta changes.

---

## EPIC 5: News Intelligence

**Purpose**: Build an NLP-powered news analysis system that feeds sentiment data into the scoring pipeline.

**Architecture Impact**: New module `news/`. Adds NLP pipeline, news API integration, sentiment scoring. Feeds into `ScoringEngine`.

**Estimated Complexity**: L (34 SP)

**Dependencies**: EPIC 1 (Foundation Hardening)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| N-01 | Design news intelligence module architecture | 1 SP | HIGH |
| N-02 | Integrate news API sources (NewsAPI, CryptoCompare, Twitter/X API) | 3 SP | HIGH |
| N-03 | Build news ingestion pipeline (fetch → normalize → classify → store) | 4 SP | HIGH |
| N-04 | Implement NLP sentiment analysis (finBERT or custom model for crypto) | 5 SP | HIGH |
| N-05 | Build news classification system (by asset, category, impact level) | 3 SP | HIGH |
| N-06 | Create news-to-signal bridge → sentiment scoring feed into pipeline | 2 SP | HIGH |
| N-07 | Implement news source quality scoring and reputation system | 2 SP | MEDIUM |
| N-08 | Add news intelligence API endpoints | 2 SP | MEDIUM |
| N-09 | Build News Intelligence frontend (news feed, sentiment charts) | 3 SP | MEDIUM |
| N-10 | Add historical news backtesting capability | 3 SP | LOW |
| N-11 | Implement real-time news alerting and notification system | 2 SP | MEDIUM |
| N-12 | Add news impact analysis on price movement | 2 SP | MEDIUM |

### Risks
- API costs for news/commercial data feeds.
- NLP accuracy in crypto domain is challenging due to slang and market manipulation.
- Twitter/X API changes and restrictions.

### Acceptance Criteria
- [ ] News ingested from 3+ sources with deduplication.
- [ ] Sentiment score per asset with confidence level.
- [ ] News events linked to price movements in backtest.
- [ ] News sentiment integrated into `ScoringEngine` as optional component.
- [ ] News frontend with filterable feed and sentiment timeline.

---

## EPIC 6: Whale Intelligence

**Purpose**: Build on-chain whale tracking system to detect and alert on large wallet movements.

**Architecture Impact**: New module `whale/`. Integrates blockchain data providers. May use existing `notifications/` system.

**Estimated Complexity**: L (34 SP)

**Dependencies**: EPIC 1 (Foundation Hardening)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| W-01 | Design whale intelligence module architecture | 1 SP | HIGH |
| W-02 | Integrate on-chain data provider (Arkham, Nansen, Etherscan API) | 3 SP | HIGH |
| W-03 | Build whale wallet tracker (track top 1000 wallets per chain) | 4 SP | HIGH |
| W-04 | Implement large transaction detection (>$100K, >$1M, >$10M tiers) | 3 SP | HIGH |
| W-05 | Build exchange flow tracking (exchange inflows/outflows) | 3 SP | HIGH |
| W-06 | Implement whale accumulation/distribution detection | 4 SP | HIGH |
| W-07 | Create whale-to-signal bridge → trade signals from whale activity | 2 SP | MEDIUM |
| W-08 | Add whale alerting system via notifications/WebSocket | 2 SP | HIGH |
| W-09 | Build Whale Intelligence API endpoints | 2 SP | MEDIUM |
| W-10 | Build Whale Dashboard frontend (whale movements, flow charts) | 3 SP | MEDIUM |
| W-11 | Add multi-chain support (Ethereum, Solana, BSC, Arbitrum) | 5 SP | LOW |
| W-12 | Implement whale correlation with price movements | 2 SP | MEDIUM |

### Risks
- On-chain data APIs are expensive at scale.
- Multi-chain support is complex (different RPCs, address formats).
- Privacy concerns around wallet tracking.

### Acceptance Criteria
- [ ] Tracks top 1000 wallets across 2+ chains.
- [ ] Real-time alerts for transactions >$100K.
- [ ] Exchange flow dashboard with accumulation/distribution signals.
- [ ] Whale activity correlated with price movements.
- [ ] Whale signals generated and fed into pipeline.

---

## EPIC 7: Probability Engine

**Purpose**: Build a probability-weighted outcome prediction system for trade candidates. Replace the current simple threshold-based approval system.

**Architecture Impact**: High. New module `probability/`. Changes `ConfidenceEngine` and `ScoringEngine`. May require ML model training pipeline.

**Estimated Complexity**: XL (55 SP)

**Dependencies**: EPIC 2 (Execution Engine Optimization), EPIC 4 (Market Intelligence)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| P-01 | Design probability engine architecture | 2 SP | HIGH |
| P-02 | Build historical trade data export pipeline (for ML training) | 3 SP | HIGH |
| P-03 | Implement feature engineering for ML (market features, scoring features) | 5 SP | HIGH |
| P-04 | Build ML model training pipeline (train/test/validate) | 5 SP | HIGH |
| P-05 | Implement model serving (ONNX or pickle with versioning) | 3 SP | HIGH |
| P-06 | Build Bayesian probability estimation (non-ML baseline) | 3 SP | MEDIUM |
| P-07 | Implement Monte Carlo simulation for trade outcomes | 4 SP | HIGH |
| P-08 | Build outcome distribution analysis (win rate, R:R distribution) | 3 SP | MEDIUM |
| P-09 | Integrate probability into `ConfidenceEngine` as decision factor | 2 SP | HIGH |
| P-10 | Add probability API endpoints | 2 SP | MEDIUM |
| P-11 | Build Probability frontend (probability charts, distribution curves) | 3 SP | MEDIUM |
| P-12 | Add A/B testing framework for model comparison | 3 SP | MEDIUM |
| P-13 | Implement model monitoring (drift detection, accuracy tracking) | 3 SP | HIGH |
| P-14 | Build automated model retraining pipeline | 2 SP | MEDIUM |
| P-15 | Add feature importance analysis and explainability | 2 SP | MEDIUM |

### Risks
- ML model quality depends on volume of historical trade data (limited from paper trading).
- Regulatory considerations for AI-based investment decisions.
- Model overfitting is a significant risk with financial data.

### Acceptance Criteria
- [ ] Probability engine predicts trade outcome with >60% accuracy on test data.
- [ ] Monte Carlo simulation shows expected value distribution.
- [ ] ConfidenceEngine uses probability as weighted factor.
- [ ] Model versioning and rollback capability.
- [ ] Feature importance dashboard shows top predictive features.

---

## EPIC 8: Elite Terminal

**Purpose**: Upgrade the frontend trading terminal to professional-grade with real-time multi-chart, advanced order types, and professional workspace.

**Architecture Impact**: Medium. Frontend-focused. Backend changes limited to API enhancements for new trading features.

**Estimated Complexity**: L (34 SP)

**Dependencies**: EPIC 1 (Foundation Hardening)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| T-01 | Upgrade chart engine with multi-timeframe, multi-symbol support | 4 SP | HIGH |
| T-02 | Implement advanced order types (OCO, trailing stop, bracket orders) | 4 SP | HIGH |
| T-03 | Build professional workspace with undocked windows | 3 SP | MEDIUM |
| T-04 | Add real-time portfolio tracking with P&L heatmaps | 2 SP | HIGH |
| T-05 | Implement trade journal with tagging, screenshots, and grading | 3 SP | MEDIUM |
| T-06 | Build execution analytics dashboard (slippage, fill rate, latency) | 3 SP | MEDIUM |
| T-07 | Add advanced charting tools (drawing tools, indicators, alert lines) | 4 SP | MEDIUM |
| T-08 | Implement keyboard-first navigation with custom shortcuts | 2 SP | MEDIUM |
| T-09 | Build alert system (price alerts, indicator alerts, pattern alerts) | 3 SP | HIGH |
| T-10 | Add multi-monitor support with detached panels | 2 SP | LOW |
| T-11 | Implement layout presets and session state persistence | 2 SP | MEDIUM |
| T-12 | Upgrade WebSocket connection to support reconnection with state recovery | 2 SP | HIGH |

### Risks
- Chart engine performance with 10+ symbols open simultaneously.
- Undocked windows require browser popup handling.

### Acceptance Criteria
- [ ] Chart supports 6 timeframes, multiple symbols, drawing tools.
- [ ] OCO and trailing stop orders available in paper trading.
- [ ] Professional workspace with resizable, detachable panels.
- [ ] Keyboard shortcuts for all major actions.
- [ ] Alerts trigger via WebSocket and notification center.

---

## EPIC 9: Portfolio Intelligence

**Purpose**: Upgrade portfolio tracking from basic metrics to comprehensive portfolio intelligence with risk analytics, optimization, and what-if scenarios.

**Architecture Impact**: Medium. Extends `services/portfolio_service.py` and frontend portfolio pages.

**Estimated Complexity**: M (21 SP)

**Dependencies**: EPIC 1 (Foundation Hardening)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| PI-01 | Build portfolio risk analytics (VaR, CVaR, Sharpe, Sortino, Calmar) | 3 SP | HIGH |
| PI-02 | Implement portfolio optimization (mean-variance, risk parity, max Sharpe) | 4 SP | HIGH |
| PI-03 | Build correlation analysis across all tracked assets | 2 SP | HIGH |
| PI-04 | Add drawdown analysis with recovery time tracking | 2 SP | MEDIUM |
| PI-05 | Implement what-if scenario analysis | 3 SP | MEDIUM |
| PI-06 | Build performance attribution (asset allocation, timing, selection) | 3 SP | HIGH |
| PI-07 | Add portfolio rebalancing recommendations | 2 SP | MEDIUM |
| PI-08 | Build Portfolio Intelligence API endpoints | 2 SP | MEDIUM |
| PI-09 | Upgrade Portfolio frontend with advanced charts and reports | 3 SP | MEDIUM |

### Risks
- Portfolio optimization requires sufficient historical data.
- Real-time portfolio tracking requires low-latency price feeds.

### Acceptance Criteria
- [ ] Portfolio dashboard shows VaR (95%, 99%), Sharpe, Sortino, Calmar ratios.
- [ ] Mean-variance optimization suggests optimal allocation.
- [ ] Correlation matrix across all positions.
- [ ] Drawdown chart with recovery timeline.
- [ ] What-if scenario: "What happens if BTC drops 20%?"

---

## EPIC 10: AI Assistant

**Purpose**: Build an AI-powered assistant that provides natural language querying, trade explanations, market insights, and decision support.

**Architecture Impact**: High. New module `assistant/`. Integrates LLM API. Provides natural language interface across all system data.

**Estimated Complexity**: XL (55 SP)

**Dependencies**: EPIC 1 (Foundation Hardening), EPIC 4 (Market Intelligence), EPIC 7 (Probability Engine)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| A-01 | Design AI assistant architecture (LLM integration, prompt system) | 2 SP | HIGH |
| A-02 | Integrate LLM API (OpenAI, Anthropic, or local model via Ollama) | 3 SP | HIGH |
| A-03 | Build prompt engineering framework (system prompts, context assembly) | 4 SP | HIGH |
| A-04 | Implement trade explanation engine ("Why was this trade approved?") | 3 SP | HIGH |
| A-05 | Build market Q&A system (natural language queries about market state) | 4 SP | HIGH |
| A-06 | Implement portfolio analysis with natural language reporting | 3 SP | HIGH |
| A-07 | Build risk alert explanations with actionable recommendations | 3 SP | MEDIUM |
| A-08 | Add signal generation via natural language commands | 3 SP | MEDIUM |
| A-09 | Implement conversation memory and context management | 2 SP | MEDIUM |
| A-10 | Build AI Assistant API endpoints (chat, explain, analyze) | 2 SP | HIGH |
| A-11 | Build AI Chat frontend (chat interface with sources and confidence) | 4 SP | HIGH |
| A-12 | Add voice interface capability (speech-to-text for commands) | 3 SP | LOW |
| A-13 | Implement RAG (Retrieval-Augmented Generation) for market knowledge | 4 SP | MEDIUM |
| A-14 | Build usage monitoring and cost tracking for LLM API calls | 2 SP | MEDIUM |

### Risks
- LLM API costs at scale (prompt engineering can reduce but not eliminate).
- Latency: LLM response time may exceed acceptable UX thresholds.
- Hallucinations in trade recommendations could lead to losses.
- Data privacy: sensitive portfolio data sent to third-party LLM APIs.

### Acceptance Criteria
- [ ] Assistant answers natural language questions about market state.
- [ ] "Why was trade X opened?" generates human-readable explanation.
- [ ] "What's my portfolio risk?" generates natural language summary.
- [ ] Assistant can create signals based on natural language commands.
- [ ] Chat interface with message history and confidence indicators.
- [ ] RAG system retrieves relevant market context for answers.

---

## EPIC 11: Production Readiness

**Purpose**: Make the platform production-ready with monitoring, testing, documentation, and deployment automation.

**Architecture Impact**: Low. Operational improvements across all layers.

**Estimated Complexity**: M (21 SP)

**Dependencies**: EPIC 1 (Foundation Hardening), EPIC 2 (Execution Engine Optimization)

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| PR-01 | Create missing backup script (`scripts/backup.sh`) for production | 1 SP | HIGH |
| PR-02 | Add integration test for end-to-end pipeline (Signal → Pipeline → Loop → Trade → Paper) | 3 SP | CRITICAL |
| PR-03 | Add CI/CD deployment step (Docker build + push + deploy to staging) | 3 SP | HIGH |
| PR-04 | Add integration test coverage for API routes (request/response contract tests) | 3 SP | HIGH |
| PR-05 | Add load testing suite (locust or k6) for API endpoints | 2 SP | MEDIUM |
| PR-06 | Add frontend E2E tests (Playwright or Cypress) for critical flows | 3 SP | HIGH |
| PR-07 | Create runbooks for common operational tasks | 2 SP | MEDIUM |
| PR-08 | Add automated schema validation in CI (OpenAPI spec diff checker) | 1 SP | MEDIUM |
| PR-09 | Implement structured error responses across all API endpoints | 2 SP | MEDIUM |
| PR-10 | Add Git hooks (pre-commit linting, type checking) | 1 SP | MEDIUM |

### Risks
- E2E tests require running environment (DB, API, frontend) — CI complexity.
- Load testing must not affect production exchanges.

### Acceptance Criteria
- [ ] `scripts/backup.sh` exists and creates encrypted S3 backups.
- [ ] CI pipeline deploys to staging environment on merge to `main`.
- [ ] API route contract tests run in CI.
- [ ] Frontend E2E tests cover dashboard, trading, and portfolio flows.
- [ ] Load test report shows API handles 1000 req/s.
- [ ] Pre-commit hooks run lint + type check.

---

## EPIC 12: Beta Launch Preparation

**Purpose**: Final integration, testing, and launch preparation for Elite Platform Beta.

**Architecture Impact**: Low. Focus on stability, UX polish, and documentation.

**Estimated Complexity**: S (13 SP)

**Dependencies**: ALL previous EPICs

### Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| B-01 | Full system integration testing (all modules together) | 3 SP | CRITICAL |
| B-02 | Security audit (penetration testing, dependency scan) | 2 SP | HIGH |
| B-03 | Performance profiling and optimization | 2 SP | HIGH |
| B-04 | UX polish pass (loading states, error states, empty states) | 2 SP | MEDIUM |
| B-05 | Documentation: API docs, user guide, architecture docs | 2 SP | HIGH |
| B-06 | Create Beta onboarding flow (signup, first trade) | 1 SP | MEDIUM |
| B-07 | Set up monitoring dashboards (Grafana) and alerting | 1 SP | HIGH |

### Risks
- Integration testing may reveal unexpected module interactions.
- Security audit may require significant remediation time.

### Acceptance Criteria
- [ ] All EPICs complete and acceptance criteria met.
- [ ] Security audit passes with no HIGH severity findings.
- [ ] API response time <200ms p95 for all endpoints.
- [ ] Documentation covers all user-facing features.
- [ ] Beta users can sign up and complete first trade in <5 minutes.

---

## Summary: Epic Effort Estimates

```
EPIC        SP   WEEKS*  TEAM
───         ──   ─────   ────
EPIC 1       8    2      1 BE
EPIC 2      13    3      1 BE
EPIC 3      21    3      1 BE + 1 FE
EPIC 4      21    3      1 BE + 1 FE
EPIC 5      34    4      2 BE + 1 FE
EPIC 6      34    4      2 BE + 1 FE
EPIC 7      55    6      2 BE + 1 FE + 1 ML
EPIC 8      34    4      2 FE
EPIC 9      21    3      1 BE + 1 FE
EPIC 10     55    6      2 BE + 1 FE + 1 AI
EPIC 11     21    3      1 BE + 1 FE
EPIC 12     13    2      1 BE + 1 FE
───────     ──    ──     ──────────────
TOTAL      330   43 weeks (~10 months)

* Assumes 5 SP/week per developer
```

---

## Dependency Graph

```
EPIC 1 ── Foundation Hardening
  │
  ├──► EPIC 2 ── Execution Engine Optimization
  │     │
  │     ├──► EPIC 3 ── Elite Scanner
  │     │
  │     └──► EPIC 7 ── Probability Engine
  │
  ├──► EPIC 4 ── Market Intelligence
  │     │
  │     ├──► EPIC 7 ── Probability Engine
  │     └──► EPIC 10 ─ AI Assistant
  │
  ├──► EPIC 5 ── News Intelligence
  │
  ├──► EPIC 6 ── Whale Intelligence
  │
  ├──► EPIC 8 ── Elite Terminal
  │
  └──► EPIC 9 ── Portfolio Intelligence

EPIC 11 ── Production Readiness
  │
  └──► EPIC 12 ── Beta Launch
```

---

*End of ROADMAP.md*
