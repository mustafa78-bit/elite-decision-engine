# Roadmap v1 — Production Launch

## Milestone: Foundation Hardening (Est. 1 week)

### Critical
- [ ] Fix ConfidenceEngine double-scaling math bug (BP2)
- [ ] Fix ATRr_14 typo in indicators (BP3)
- [ ] Add pandas_ta to requirements.txt
- [ ] Increase JWT secret key to 32+ bytes

### High
- [ ] Add ForeignKey constraint on Trade.signal_id
- [ ] Add rate limiting to all public API endpoints
- [ ] Wire real dependencies into ExplanationService
- [ ] Wire real AI sources into CoordinatorService

### Medium
- [ ] Add query pagination on all list endpoints
- [ ] Remove dead code artifacts (DC1-9)
- [ ] Resolve datetime.utcnow() deprecation across entire codebase
- [ ] Condition WebSocket broadcast on active clients

### Low
- [ ] Split test_edge_cases.py into focused modules
- [ ] Split test_api_routes.py into per-route files
- [ ] Add CI/CD pipeline configuration
- [ ] Add health check endpoints
- [ ] Add structured JSON logging
- [ ] Add Prometheus metrics endpoint

## v1.0 Release Criteria
- [ ] All critical bugs fixed
- [ ] Test suite 100% passing
- [ ] API documentation complete
- [ ] Rate limiting operational
- [ ] DB constraints validated
- [ ] Deployment documentation ready
