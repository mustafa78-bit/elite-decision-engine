# Roadmap — Next Steps

## Release 1.0 (Production Launch)

### Phase 1: Foundation Hardening (Est. 1 week)

- [ ] Add ForeignKey constraints + SQLAlchemy relationships to all models
- [ ] Add connection pooling for database sessions
- [ ] Fix `ConfidenceEngine` double-scaling math bug (BP2)
- [ ] Fix `ATRr_14` typo (BP3)
- [ ] Add `pandas_ta` to `requirements.txt`
- [ ] Increase JWT secret key to 32+ bytes
- [ ] Add rate limiting to all API endpoints

### Phase 2: Performance Optimization (Est. 1 week)

- [ ] Paginate all list endpoints (trades, signals, portfolio)
- [ ] Optimize portfolio_engine.py to use filtered SQL queries
- [ ] Condition websocket broadcast on active clients
- [ ] Resolve all `datetime.utcnow()` deprecation warnings
- [ ] Add query profiling middleware
- [ ] Add DB index on frequently filtered columns (status, created_at)

### Phase 3: Test Infrastructure (Est. 3 days)

- [ ] Split test_edge_cases.py into focused test modules
- [ ] Split test_api_routes.py into per-route test files
- [ ] Add integration tests that exercise the full pipeline
- [ ] Add E2E test with real database
- [ ] Add CI/CD pipeline configuration

### Phase 4: Documentation & Observability (Est. 3 days)

- [ ] Add OpenAPI doc customization (summary, description, tags)
- [ ] Add health check endpoints for all external dependencies
- [ ] Add structured logging (JSON format for log aggregation)
- [ ] Add metrics endpoint (prometheus or similar)
- [ ] Add startup assertions for all env vars

## Release 1.1 (Feature)

### Live Trading

- [ ] Wire live exchange adapters into ExecutionLoop
- [ ] Add live balance monitoring
- [ ] Add real-time order status tracking
- [ ] Add circuit breakers for exchange errors
- [ ] Add position reconciliation

### Intelligence Expansion

- [ ] Wire real data sources into CoordinatorService
- [ ] Wire real engine dependencies into ExplanationService
- [ ] Add on-chain analytics integration
- [ ] Add social sentiment scoring
- [ ] Add regime detection service
- [ ] Add automated strategy parameter optimization

### UI/UX

- [ ] Build web dashboard frontend
- [ ] Add real-time charting
- [ ] Add trade history explorer
- [ ] Add performance dashboard
- [ ] Add alert/notification management
- [ ] Add mobile notification support

## Release 2.0 (Enterprise)

- [ ] Multi-user support with role-based access
- [ ] Team workspaces
- [ ] Audit logging
- [ ] API key management
- [ ] Webhook integrations
- [ ] Custom strategy builder
- [ ] Backtesting as a service
- [ ] Strategy marketplace
