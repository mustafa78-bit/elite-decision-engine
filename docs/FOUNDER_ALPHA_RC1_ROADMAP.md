# Elite Decision Engine
## Founder Alpha RC1 Practical Engineering Roadmap

This roadmap transforms previous audit findings, system boundaries, and execution runtime observations into a practical, highly prioritized, and implementation-focused 3-Sprint Engineering Roadmap.

---

# SPRINT 1: RELEASE BLOCKERS (Stabilization, Critical Bug Fixes & DB Consistency)

### 1. Sprint Goal
Eliminate all critical bugs, logging format string exceptions, double-scaling decision engines, and schema constraints to establish a completely stable, green test-suite, and fully predictable trading behavior.

### 2. Tasks

*   **Task S1-01: Resolve Logging Filter Type Conversion Bug**
    *   **Priority**: Critical
    *   **Estimated Effort**: 1.5 Story Points (ideal dev-days)
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Resolves a critical regression where the customized sensitive data filter `_SensitiveDataFilter` converts numerical logger parameters to strings. When formatting messages containing `%d`, Python's logger throws a `TypeError: %d format: a real number is required, not str`. Fixing this resolves all 193 failing pytest integration cases instantly.
*   **Task S1-02: Correct the `ConfidenceEngine` Double-Scaling Bug**
    *   **Priority**: Critical
    *   **Estimated Effort**: 1.0 Story Points
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Fixes the double-scaling issue where confidence calculations are improperly multiplied by 100, forcing every single trade proposal to evaluate as `STRONG_APPROVE`. Aligning confidence to a strict 0–100 boundary restores active filtering control.
*   **Task S1-03: Correct Indicator Fallback Key Resolution in `IndicatorEngine`**
    *   **Priority**: High
    *   **Estimated Effort**: 1.0 Story Points
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Normalizes indicator retrieval by ensuring the pipeline's pandas-ta calls gracefully fall back and search for standard prefixes (e.g., matching both `ATRr_14` and `ATR_14`), eliminating uncaught `KeyError` exceptions that yield 0-value scores.
*   **Task S1-04: Resolve SQLite Schema Constraints and Duplicate Declarations**
    *   **Priority**: High
    *   **Estimated Effort**: 1.5 Story Points
    *   **Dependencies**: None
    *   **Risk**: Medium
    *   **Expected Impact**: Integrates missing database constraints (such as `Trade.signal_id` ForeignKey relational cascades) and removes duplicate `update_signal_status()` method references inside `database.py` to prevent circular imports or dead code.

### 3. Files Expected to Change

*   **Backend Files**:
    *   `logging_config.py` (Modify `_SensitiveDataFilter` to preserve argument types during scrubbing)
    *   `core/confidence_engine.py` (Remove extra confidence double-multipliers)
    *   `market_data/indicators.py` (Refine `IndicatorEngine` column lookup strategies)
    *   `database.py` (Add missing foreign keys and clean up duplicate methods)
*   **Frontend Files**: None (Purely backend stabilization)
*   **Infrastructure/Configuration Files**: None
*   **Documentation Files**: `KNOWN_LIMITATIONS.md` (Update bug statuses)

### 4. Testing Requirements

*   **Backend**: Run the full suite `python -m pytest` ensuring 100% test collection passes (all 1326 test cases green).
*   **Frontend**: Verify that the Overview workstation page dashboard loads and doesn't trigger blank card failures.
*   **Authentication**: Assert that user logins succeed without raising database pool errors.
*   **WebSocket**: Verify that connecting multiple clients to WebSocket rooms (e.g., `/health/ai`, `/council/evaluate`) does not crash logging handlers.
*   **AI**: Verify that simulated confidence calculations yield correct `APPROVE` / `WATCH` / `REJECT` divisions based on actual data.
*   **Council**: Run the AI agent evaluation sequence to ensure generated ratings reflect real metrics.
*   **OLLO**: Verify OLLO's message parsing works under varying confidence values.
*   **Database**: Verify SQLite schema structure enforces strict constraint checks on duplicate user insertions or orphan trades.
*   **Docker**: Perform a local test run of the server within standard docker-compose to ensure it initializes tables.
*   **CI**: Verify that GitHub actions workflow compiles cleanly.

### 5. Acceptance Criteria
*   ✓ Zero formatting `TypeError` warnings or crashes in logs or tests.
*   ✓ Complete backend test suite passes (1326/1326 passing).
*   ✓ Database constraints are strictly relational with no duplicate methods.
*   ✓ Confidence score outputs stay accurately bound within the 0 to 100 percentage range.

### 6. Possible Regressions
*   **Issue**: Adjusting argument conversions in `_SensitiveDataFilter` might accidentally bypass log redaction for integers that match sensitive formats.
*   **Mitigation**: Modify the filter to stringify for pattern checking but strictly maintain original types in `record.args` unless an actual sensitive match is redacted.

---

# SPRINT 2: PRODUCTION HARDENING (Security, Reliability, Monitoring & Infrastructure)

### 1. Sprint Goal
Harden the platform's execution safety, secure the docker build layers, eliminate sensitive configuration defaults, and introduce granular rate-limiting controls.

### 2. Tasks

*   **Task S2-01: Create Missing Container and Operational Files**
    *   **Priority**: High
    *   **Estimated Effort**: 1.5 Story Points
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Creates `.dockerignore` to shrink build context sizes (excluding `node_modules`, local `.env`, and python cache files), creates `deploy/init-db.sql` for automated PostgreSQL/SQLite initialization, and creates the backup automation script `scripts/backup.sh`.
*   **Task S2-02: Pin Python Dependencies & Refactor Requirements**
    *   **Priority**: High
    *   **Estimated Effort**: 1.5 Story Points
    *   **Dependencies**: None
    *   **Risk**: Medium
    *   **Expected Impact**: Pins all unpinned package versions in `requirements.txt` to lock-in identical execution environments. Groups developer and production dependencies cleanly using a standard `pyproject.toml`.
*   **Task S2-03: Secure Token Environment & Enforce Key Minimums**
    *   **Priority**: High
    *   **Estimated Effort**: 1.0 Story Points
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Removes insecure hardcoded fallback variables (such as the default `change-me-in-production` token in `docker-compose.yml`) and enforces a minimum key size constraint of 32 bytes for JWT keys to secure communications.
*   **Task S2-04: Configure Per-Route Rate Limiting**
    *   **Priority**: Medium
    *   **Estimated Effort**: 1.5 Story Points
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Updates `slowapi` rate limiting configs to implement strict, secure request limits on write paths (e.g. `/auth/login` restricted to 10 requests/minute) and comfortable higher thresholds for telemetry paths.

### 3. Files Expected to Change

*   **Backend Files**:
    *   `config.py` (Add secure environment validator rules)
    *   `api/rate_limit.py` (Add granular slowapi limits)
    *   `auth/jwt.py` (Validate token secret key length)
*   **Frontend Files**: None (Ensure local builds still load the local rate limit middleware)
*   **Infrastructure/Configuration Files**:
    *   `.dockerignore` (Create from scratch)
    *   `requirements.txt` (Pin package versions with hashes)
    *   `pyproject.toml` (Add dependencies metadata)
    *   `deploy/init-db.sql` (Create schema seeding)
    *   `scripts/backup.sh` (Create database backup routine)
    *   `docker-compose.yml` (Remove insecure hardcoded secrets)
    *   `docker-compose.prod.yml` (Reference clean init files)
*   **Documentation Files**: `PRODUCTION_CHECKLIST.md` (Update operational metrics)

### 4. Testing Requirements

*   **Backend**: Test rate limiters by triggering concurrent requests and verifying HTTP 429 status returns on overflow.
*   **Frontend**: Verify that frontend pages show clear, non-cryptic error states when hitting rate limits.
*   **Authentication**: Confirm login blocks non-compliant or too-frequent login requests.
*   **WebSocket**: Verify rate limits do not block standard real-time frame streaming.
*   **AI**: None.
*   **Council**: None.
*   **OLLO**: None.
*   **Database**: Run manual seeding routines with `init-db.sql` to verify schema compatibility.
*   **Docker**: Perform multi-stage production builds and confirm image output is compact and excludes local environment assets.
*   **CI**: Verify the automated workflow runs successfully on docker registry targets.

### 5. Acceptance Criteria
*   ✓ Zero unpinned Python dependency vulnerabilities.
*   ✓ Multi-stage Docker builds complete successfully, leaving behind no unnecessary build artifacts.
*   ✓ Insecure default secrets are completely disabled; server crashes immediately on launch if default values are used in production.
*   ✓ Granular, per-route rate limiting behaves correctly across all endpoints.

### 6. Possible Regressions
*   **Issue**: Excessively strict rate limiting might block client-side polling or websocket initialization under peak dashboard loading.
*   **Mitigation**: Set higher request quotas on passive metrics APIs, only tightening limits on login and trade control routes.

---

# SPRINT 3: TECHNICAL DEBT, PERFORMANCE & DEVELOPER EXPERIENCE

### 1. Sprint Goal
Address remaining developer friction, optimize chunk-splitting to speed up frontend loading, future-proof datetimes, and convert the blocking execution loop into an async pattern.

### 2. Tasks

*   **Task S3-01: Refactor Main Loop from Thread-Blocking to Async Task**
    *   **Priority**: High
    *   **Estimated Effort**: 2.5 Story Points
    *   **Dependencies**: Sprints 1 & 2
    *   **Risk**: High
    *   **Expected Impact**: Concurrently scales the single-threaded event loop by converting `DecisionEngine.run()` from a blocking `while True: sleep()` model to an asynchronous cooperative task (`asyncio.sleep`). This prevents background calculations from holding up API request servicing.
*   **Task S3-02: Upgrade Deprecated `utcnow()` Implementations**
    *   **Priority**: Medium
    *   **Estimated Effort**: 1.5 Story Points
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Replaces all 32 occurrences of deprecated `datetime.utcnow()` with offset-aware timezone-naive conversions (or modern `datetime.now(timezone.utc)`) to future-proof the application for Python 3.14+ compatibility.
*   **Task S3-03: Optimize Frontend Assets & Vite Chunk Splitting**
    *   **Priority**: Medium
    *   **Estimated Effort**: 1.5 Story Points
    *   **Dependencies**: None
    *   **Risk**: Low
    *   **Expected Impact**: Configures Vite asset boundaries to split oversized packages (such as Lucide and complex Chart engines) into isolated vendor chunks, reducing first-load dashboard chunk size from 746KB to under 500KB.

### 3. Files Expected to Change

*   **Backend Files**:
    *   `core/engine.py` (Convert background loops to async)
    *   `services/kpi_service.py` (Clean up import hacks)
    *   Various database models, routes, and tests utilizing datetime libraries
*   **Frontend Files**:
    *   `frontend/vite.config.ts` (Implement explicit manual chunk splitting rules)
*   **Infrastructure/Configuration Files**: None
*   **Documentation Files**: `TECHNICAL_DEBT.md` (Log resolved architecture debt)

### 4. Testing Requirements

*   **Backend**: Verify background loops continue trading reliably without causing async lockouts or race conditions in DB sessions.
*   **Frontend**: Verify Vite compilation completes cleanly and generates isolated chunk files under the strict 500KB limit.
*   **Authentication**: Validate that lazy-routed pages function correctly under token-expired scenarios.
*   **WebSocket**: Verify that WebSocket updates continue streaming continuously alongside active async background processing.
*   **AI**: Confirm AI health and signal generation processes are fully integrated into async tasks.
*   **Council**: Assert multi-agent evaluations are non-blocking.
*   **OLLO**: Verify real-time workspace suggestions are returned instantly without loop lag.
*   **Database**: Check that datetime values saved to SQLite tables do not suffer from naive vs timezone-aware comparison `TypeErrors`.
*   **Docker**: Build production container image and verify optimized bundle is shipped.
*   **CI**: Ensure all static quality and validation checks pass cleanly.

### 5. Acceptance Criteria
*   ✓ The background main engine loop operates co-operatively without thread locking.
*   ✓ All frontend build chunk assets remain below the 500KB size limit.
*   ✓ Full test suite passes without any datetime deprecation warnings.

### 6. Possible Regressions
*   **Issue**: Running background loops asynchronously might trigger concurrent SQLite locked errors when simultaneous database sessions attempt to execute write queries.
*   **Mitigation**: Standardize all database operations using transactional `@contextmanager` scopes (`session_scope()`) to ensure locks are resolved immediately.

---

# DELIVERABLES

### 1. Overall Timeline
*   **Estimated Duration**: **3 Weeks** (Total of **14 Story Points** of effort).
*   **Resource Allocation**: 1 Experienced Full-Stack Engineer working full-time.

---

### 2. Risk Assessment

*   **Remaining Risks After Sprint 1**: **Low-to-Medium**. Core runtime bugs and test failures will be completely cleared. Remaining risks will center around container deployments, loose dependency trees, and unhardened token configurations.
*   **Remaining Risks After Sprint 2**: **Low**. The platform will be fully protected, secure, and reproducible on remote container servers. The only remaining risks will be background thread utilization and minor bundle performance warnings.
*   **Remaining Risks After Sprint 3**: **Negligible**. Code cleanliness, bundle delivery sizes, timezone deprecations, and concurrent execution loops will be optimized. The platform will operate as a production-hardened system.

---

### 3. Production Readiness Score

*   **Score after Sprint 1**: **6.5 / 10** (Stable local environment, zero test failures, correct pipeline calculations; but missing container isolation and rate limiting).
*   **Score after Sprint 2**: **8.5 / 10** (Secure, pinned dependencies, robust brute-force protection, production docker compose configurations; but background engine remains blocking).
*   **Score after Sprint 3**: **9.8 / 10** (Asynchronous background engine loop, high-performance front-end loading, clean future-proof datetime codebase).

---

### 4. Founder Alpha Readiness

**State**: **READY FOR CLOSED FOUNDER ALPHA**

#### Technical Justification:
The platform is functionally complete, with premium dark navy workstation dashboard designs, fully functional bi-directional workspace navigation, complete AI council integrations, and robust real-time communication layers.

Launching public beta access right now is deferred strictly to allow for production operations hardening (Sprint 2) and main-loop optimization (Sprint 3) to prevent early system bottlenecks under high traffic volumes. However, immediately after resolving the critical release blockers in **Sprint 1**, the platform is in a perfect state to be securely deployed for **Closed Founder Alpha** testing with VIP institutional operators.

---

# FINAL SECTION

### Launch Approval Decision

"If you were personally responsible for this repository going live next month, would you approve the launch after Sprint 3?"

**YES, WITH CONDITIONS**

#### Detailed Technical Justification:
Following the completion of Sprint 3, the codebase will have successfully resolved every historical blocker, security gap, performance bottleneck, and architectural vulnerability identified across all audits.

However, before approving the production launch to go live next month, the following three institutional conditions must be strictly satisfied:

1.  **Mandatory Secret Audit**: A manual configuration check must be completed to guarantee that all environment tokens (`JWT_SECRET`, exchange private keys, API secrets) are securely retrieved from a secure secret store (such as HashiCorp Vault, AWS Secrets Manager, or Doppler) rather than stored in plain-text `.env` config files on production servers.
2.  **Mock Exchange Load-Test Pass**: The system must run continuously on a Hyperliquid Mock/Testnet API for 72 consecutive hours to verify that the newly-implemented async loop does not trigger network connection drops or memory leaks under fast market conditions.
3.  **Third-Party API Resilience Check**: A verified sandbox dry-run must be executed to ensure the system degrades gracefully without crashing if any third-party external services (such as CoinMetrics or Glassnode) experience connection timeouts.

With these operational checks satisfied, the Elite Decision Engine is fully prepared to dominate live institutional environments with institutional reliability, high-performance execution, and premium workstation delivery.
