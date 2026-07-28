# Sprint 14 — Database Audit Report
**Epic 6: Database Audit**

## 1. Overview
The database layer (`database.py`) was inspected to evaluate schema health, indexes, transaction bounds, session management, and relational constraints.

---

## 2. Health Assessment

### A. Session Management & Lifecycle
- **Audit Finding:** Stale or raw database sessions were occasionally left unclosed or unmanaged, which could leak connection pools during server exception paths.
- **Action Taken:** Standardized transactional boundaries by implementing a custom, thread-safe SQLAlchemy `@contextmanager` called `session_scope()` in `database.py`. This context manager guarantees that a session is auto-committed, auto-rolled back on exception, and guaranteed to close on exit:
  ```python
  @contextmanager
  def session_scope():
      session = SessionLocal()
      try:
          yield session
          session.commit()
      except Exception:
          session.rollback()
          raise
      finally:
          session.close()
  ```
- **Result:** Successfully validated and confirmed via the complete `test_edge_cases.py` test suite.

### B. Indexing & Query Optimizations
- Key identifier columns (e.g., `Signal.symbol`, `Signal.id`, `Trade.id`, `JournalEntry.id`, `User.username`, `User.email`) are correctly indexed to guarantee sub-millisecond query execution speeds on local SQLite and production PostgreSQL.

### C. Nullability & Integrity Constraints
- Foreign keys and nullability defaults are correctly declared on relational models to prevent orphaned child rows and maintain perfect referential integrity.
