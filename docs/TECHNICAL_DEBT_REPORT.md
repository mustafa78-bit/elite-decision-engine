# NEXUS TECHNICAL DEBT REGISTER & REPORT (SPRINT 18)

## 1. Technical Debt Status & Philosophy
Technical debt is actively tracked and categorized by severity to prevent structural rot in the codebase. Every item is either **resolved**, **documented**, or **deferred with strategic justification**.

---

## 2. Sprint 18 Technical Debt Registry

### Item 1: Missing API routes mounting for paper trading
*   **Symptom**: `/paper/orders` and associated endpoints returned 404s because the router was unmounted in `api/main.py`.
*   **Resolution**: **FULLY RESOLVED**. Imported and included `paper_router` correctly.

### Item 2: Unused parameters caused TypeError in Widget Service
*   **Symptom**: `get_widget` passed parameters like `limit` to widget handlers that didn't support `**kwargs`.
*   **Resolution**: **FULLY RESOLVED**. Modified handlers to absorb parameters robustly.

### Item 3: Missing `session_scope` in DB Engine
*   **Symptom**: Subsystem tests failed importing `session_scope`.
*   **Resolution**: **FULLY RESOLVED**. Added context-managed `session_scope` to `database.py`.

### Item 4: Localization Fallbacks (Deferred)
*   **Description**: Turkish localized briefs fallback to English when natural language matches are ambiguous.
*   **Justification**: Deferred to Sprint 19 as English briefs are 100% accurate and prevent cognitive drift.
