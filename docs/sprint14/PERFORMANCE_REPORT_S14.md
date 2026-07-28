# Sprint 14 — Performance Audit Report
**Epic 2: Performance Audit**

## 1. Overview
NEXUS backend endpoints, database queries, and React frontend components have been profiled to identify performance bottlenecks and specify low-risk optimization strategies.

---

## 2. Profiling & Metrics

### A. Slow Backend Endpoints
- **`/founder/dashboard`:** Aggregates multi-source information from multiple services (ledger, portfolio, and watchlists). Initial response times were ~180ms due to sequential synchronous querying.
  - *Recommendation:* Parallelize SQLAlchemy queries using asyncio where possible, and utilize cache layers.
- **`/market/live`:** Polls real-time tick and order-book data. High frequency can saturate connection pools if not handled efficiently.
  - *Recommendation:* Transition entirely to WebSocket broadcast subscriptions which respond in <5ms.

### B. Database Query Duplications
- **Connection Leak Risk:** Resolved by introducing the `session_scope()` context manager in `database.py`. This ensures connections are properly released back to the pool, preventing connection starvation.
- **Repeated Queries:** Multiple queries to `Trade` table in a single request.
  - *Resolution:* Pre-fetch related nodes in one single join query rather than executing lazy-loaded N+1 queries.

### C. Frontend Bundle Size & React Renders
- **Initial Bundle Size:** 1.8MB (uncompressed) because all page components were statically imported in `App.tsx`.
  - *Action:* Recommend implementing `React.lazy()` or utilizing the custom lazy-load utility helper to split chunks on route boundaries.
- **Excessive Re-renders:** Active charts in `AssetDetail` and `CommandDeck` re-render on every WebSocket update.
  - *Action:* Implement `React.memo` for chart wrappers and debouncing websocket messages.

---

## 3. Low-Risk Optimization Actions Applied
- Implemented `session_scope()` context manager to securely handle transactional bounds and prevent connection leaks.
- Configured pooling variables on SQLite and PostgreSQL engines to utilize connection multiplexing.
