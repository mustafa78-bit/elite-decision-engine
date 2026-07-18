# Next Phase: Production Launch

## Phase 1: Foundation Fixes (Week 1)

### Critical Bugs
- [ ] Fix `ConfidenceEngine` math bug — double-scaling `confidence * 100` causes `STRONG_APPROVE` for every signal (`core/confidence_engine.py`)
- [ ] Fix `ATRr_14` typo in `market_data/indicators.py:25` — rename to `ATR_14`
- [ ] Add `pandas_ta` to `requirements.txt`

### Database
- [ ] Add ForeignKey constraints to all models (especially `Trade.signal_id`)
- [ ] Add SQLAlchemy relationships (lazy=selectin for performance)
- [ ] Create Alembic migration framework in `migrations/`
- [ ] Add connection pooling optimization for PostgreSQL
- [ ] Remove duplicate `update_signal_status()` function

## Phase 2: Security Hardening (Week 2)

### Authentication
- [ ] Move auth tokens from `localStorage` to httpOnly cookies
- [ ] Implement CSRF protection (double-submit cookie pattern)
- [ ] Add account lockout after N failed login attempts
- [ ] Implement TOTP-based MFA
- [ ] Extend JWT key to 32+ bytes

### API Security
- [ ] Add per-route rate limiting (strict on auth, moderate on data endpoints)
- [ ] Implement Content-Security-Policy monitoring/reporting
- [ ] Add API key authentication for external integrations
- [ ] Add encryption-at-rest for sensitive trade data

## Phase 3: Infrastructure (Week 3)

### Docker & Deployment
- [ ] Finalize `Dockerfile.prod` with multi-stage build
- [ ] Create `.dockerignore` optimized for production
- [ ] Add backup scripts for PostgreSQL
- [ ] Set up GitHub Actions CI/CD pipeline
- [ ] Add dependency scanning (pip-audit, npm audit)

### Monitoring
- [ ] Integrate Prometheus metrics endpoint
- [ ] Add Grafana dashboards
- [ ] Set up structured log aggregation (Loki/ELK)
- [ ] Configure uptime monitoring
- [ ] Set up incident alerting (PagerDuty/OpsGenie)

## Phase 4: Performance (Week 4)

### API Optimization
- [ ] Add pagination to all list endpoints (limit/offset)
- [ ] Add database indexes for common query patterns
- [ ] Optimize portfolio/analytics queries (avoid full table scans)
- [ ] Implement response caching for expensive endpoints

### Frontend Optimization
- [ ] Implement virtual scrolling for large lists
- [ ] Add service worker for offline capability
- [ ] Optimize bundle with further code splitting
- [ ] Add performance monitoring (LCP, FID, CLS)

## Phase 5: Production Readiness (Week 5+)

### Testing
- [ ] Add load testing with k6 or Artillery
- [ ] Add end-to-end tests with Playwright
- [ ] Add chaos engineering experiments
- [ ] Achieve 80%+ test coverage

### Documentation
- [ ] Create API reference documentation
- [ ] Create deployment runbook
- [ ] Create disaster recovery plan
- [ ] Create user documentation

### Legal & Compliance
- [ ] Audit data retention policies
- [ ] Review GDPR/CCPA compliance
- [ ] Create privacy policy
- [ ] Create terms of service

## Quick Wins (Can be done immediately)

- [ ] Remove 24 empty `__init__.py` files
- [ ] Fix `datetime.utcnow()` → `datetime.now(timezone.utc)` across 32 locations
- [ ] Add assertions to legacy test files or remove them
- [ ] Pin Python version in requirements.txt to avoid httpx2 incompatibility
- [ ] Fix `pandas_ta` dependency in requirements.txt
