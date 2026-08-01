# Next Release Plan — v1.0

## Phase 1: Bug Fixes (Days 1-3)

- [ ] Fix `ConfidenceEngine` math bug (BP2)
- [ ] Fix `ATRr_14` typo in `market_data/indicators.py`
- [ ] Add `pandas_ta` to `requirements.txt`
- [ ] Increase JWT secret key to 32+ bytes

## Phase 2: Database Hardening (Days 4-5)

- [ ] Add ForeignKey constraint on `Trade.signal_id`
- [ ] Add database indexes on frequently filtered columns (status, created_at)
- [ ] Add connection pooling for database sessions

## Phase 3: API Hardening (Days 6-8)

- [ ] Add rate limiting middleware to all public routes
- [ ] Add pagination to list endpoints
- [ ] Add health check endpoints
- [ ] Standardize error response format

## Phase 4: Production Wiring (Days 9-12)

- [ ] Wire real exchange adapters into ExecutionLoop
- [ ] Wire real intelligence sources into CoordinatorService
- [ ] Wire real engine dependencies into ExplanationService
- [ ] Add live balance monitoring

## Phase 5: Observability (Days 13-15)

- [ ] Add structured JSON logging
- [ ] Add metrics endpoint (Prometheus)
- [ ] Add CI/CD pipeline
- [ ] Add deployment documentation
- [ ] Complete API documentation with OpenAPI

## Release Checklist

- [ ] All critical bugs resolved
- [ ] Full test suite passes (952+ tests)
- [ ] API docs published
- [ ] Rate limiting operational
- [ ] DB constraints verified
- [ ] Deployment docs reviewed
- [ ] Security audit completed
