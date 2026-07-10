# BACKLOG — Elite Decision Engine

> Future ideas only. NOT currently implemented. Prioritized for future development.

---

## High Priority

| ID | Item | Description | Source |
|----|------|-------------|--------|
| H-01 | Fix ConfidenceEngine math bug (BP2) | Double-scaling causes every signal to be STRONG_APPROVE | TECHNICAL_DEBT.md |
| H-02 | Fix ATRr_14 typo (BP3) | Breaks indicator pipeline — all data reads as zero | TECHNICAL_DEBT.md |
| H-03 | Add Alembic database migrations | Schema changes are dangerous without migration system | ROADMAP_NEXT.md |
| H-04 | Pin dependency versions in requirements.txt | Builds are not reproducible | EXECUTIVE_SUMMARY.md |
| H-05 | Create pyproject.toml | Modern Python project metadata + dev/prod dep grouping | ROADMAP.md EPIC 1 |
| H-06 | Add .dockerignore | Exclude .git, .venv, node_modules, __pycache__ | ROADMAP.md EPIC 1 |
| H-07 | Add rate limiting to API endpoints | Currently susceptible to abuse | SECURITY_HARDENING_REPORT.md |
| H-08 | Wire real data sources into ExplanationService | Currently uses stub data | TECHNICAL_DEBT.md N1 |
| H-09 | Wire real data sources into CoordinatorService | Currently uses dummy sources | TECHNICAL_DEBT.md N2 |
| H-10 | Add ForeignKey on Trade.signal_id | Orphaned trades possible | KNOWN_LIMITATIONS.md |
| H-11 | Refactor DecisionEngine to async asyncio loop | Blocking main loop cannot scale | ROADMAP.md EPIC 2 |
| H-12 | Add market data caching layer | Reduce Hyperliquid API calls by 80%+ | ROADMAP.md EPIC 2 |
| H-13 | Add API response pagination | Degraded UX with large datasets | ROADMAP.md EPIC 2 |
| H-14 | Move JWT token to httpOnly cookies | localStorage is XSS-vulnerable | SECURITY_HARDENING_REPORT.md R1 |

## Medium Priority

| ID | Item | Description | Source |
|----|------|-------------|--------|
| M-01 | Remove 32 datetime.utcnow() deprecation warnings | Python 3.14 breakage | KNOWN_LIMITATIONS.md |
| M-02 | Add pandas_ta to requirements.txt | Missing dependency causes runtime crash | TECHNICAL_DEBT.md AF1 |
| M-03 | Add API versioning prefix (/v1/) | Route organization | ROADMAP.md EPIC 1 |
| M-04 | Add database connection pooling | Performance under load | ROADMAP_NEXT.md |
| M-05 | Optimize portfolio_engine.py SQL queries | Currently loads all trades in memory | TECHNICAL_DEBT.md 6-4 |
| M-06 | Condition WebSocket broadcast on active clients | Wasted resources with no clients | TECHNICAL_DEBT.md 6-8 |
| M-07 | Add DB indexes on frequently queried columns | Performance optimization | ROADMAP_NEXT.md |
| M-08 | Add structured logging (JSON format) | Log aggregation readiness | ROADMAP_NEXT.md |
| M-09 | Add health check endpoints for all dependencies | Observability | ROADMAP_NEXT.md |
| M-10 | Split test_edge_cases.py into focused modules | 670 lines, refactoring opportunity | TECHNICAL_DEBT.md 6-9 |
| M-11 | Increase JWT secret key to 32+ bytes | Cryptographic weakness warning | KNOWN_LIMITATIONS.md |
| M-12 | Add CSRF protection | Security hardening | SECURITY_HARDENING_REPORT.md R3 |
| M-13 | Add onboarding flow for new users | User experience | RELEASE_DECISION.md |
| M-14 | Add price chart on Asset Detail page | Currently shows placeholder | RELEASE_DECISION.md |
| M-15 | Reduce bundle size below 500KB | Performance | RELEASE_DECISION.md |
| M-16 | Add backup script (scripts/backup.sh) | Operations | ROADMAP.md EPIC 11 |
| M-17 | Add CI/CD deployment pipeline | Operations | ROADMAP.md EPIC 11 |
| M-18 | Add frontend E2E tests (Playwright/Cypress) | Test coverage | ROADMAP.md EPIC 11 |
| M-19 | Add load testing suite (locust/k6) | Performance validation | ROADMAP.md EPIC 11 |

## Low Priority

| ID | Item | Description | Source |
|----|------|-------------|--------|
| L-01 | Remove 9 dead code artifacts (DC1-9) | Maintenance burden | TECHNICAL_DEBT.md |
| L-02 | Remove 24 empty __init__.py files | Python packaging standard; harmless | TECHNICAL_DEBT.md 6-5 |
| L-03 | Add ARIA attributes and keyboard navigation | Accessibility | PRODUCT_REVIEW.md |
| L-04 | Add mobile responsive design | Currently desktop-optimized | PRODUCT_REVIEW.md |
| L-05 | Add empty states for all tables | Currently show blank | PRODUCT_REVIEW.md |
| L-06 | Add loading skeletons everywhere | Inconsistent loading states | PRODUCT_REVIEW.md |
| L-07 | Add internationalization (i18n) | Global reach | PRODUCT_REVIEW.md |
| L-08 | Add error tracking (Sentry) | Observability | PRODUCTION_READINESS.md |
| L-09 | Add performance monitoring | Observability | PRODUCTION_READINESS.md |
| L-10 | Add user analytics | Product insights | PRODUCTION_READINESS.md |
| L-11 | Add OpenAPI doc customization | Developer experience | ROADMAP_NEXT.md |
| L-12 | Add Git hooks (pre-commit lint, type check) | Code quality | ROADMAP.md EPIC 11 |
| L-13 | Add automated schema validation in CI | API contract testing | ROADMAP.md EPIC 11 |

## Long Term Vision

| ID | Item | Description | Source |
|----|------|-------------|--------|
| V-01 | Elite Scanner (multi-timeframe, divergence, pattern recognition) | Signal scanning engine | ROADMAP.md EPIC 3 |
| V-02 | Market Intelligence Platform (on-chain, correlation, liquidity heatmap) | Full market analysis | ROADMAP.md EPIC 4 |
| V-03 | News Intelligence (NLP sentiment, news ingestion) | News-powered signals | ROADMAP.md EPIC 5 |
| V-04 | Whale Intelligence (on-chain tracking, whale alerts) | Whale movement signals | ROADMAP.md EPIC 6 |
| V-05 | Probability Engine (ML outcome prediction, Monte Carlo) | AI-powered trade prediction | ROADMAP.md EPIC 7 |
| V-06 | Elite Terminal (pro trading terminal, advanced charts) | Professional-grade UI | ROADMAP.md EPIC 8 |
| V-07 | Portfolio Intelligence (VaR, optimization, attribution) | Advanced portfolio analytics | ROADMAP.md EPIC 9 |
| V-08 | AI Assistant (LLM integration, natural language, RAG) | Natural language interface | ROADMAP.md EPIC 10 |
| V-09 | Live Trading (exchange integration, circuit breakers) | Real money execution | ROADMAP_NEXT.md |
| V-10 | Multi-user SaaS (roles, workspaces, audit logging) | Enterprise deployment | ROADMAP_NEXT.md |
| V-11 | Strategy Marketplace (shared strategies, community) | Platform growth | ROADMAP_NEXT.md |
| V-12 | White-label (custom branding, enterprise features) | Revenue model | ROADMAP_NEXT.md |

---

*Last updated: 2026-07-10*
