# Sprint 14 — API Audit Report
**Epic 5: API Consistency**

## 1. API Consistency Summary
An audit of every backend REST endpoint was performed to ensure uniform routing prefixes, standardized HTTP status codes, consistent JSON error payloads, and robust query parameters.

---

## 2. API Schema Consistency

### A. Endpoint Naming Conventions
- All standard REST routes use lower-case, pluralized nouns (e.g. `/journal`, `/paper/orders`, `/paper/positions`).
- Custom action-oriented paths are clearly separated (e.g. `/learning/replay` and `/learning/advisors`).

### B. HTTP Status Codes & Error Payloads
- Found and fixed a major test-expectation mismatch in `api/routes/journal.py`.
- **Finding:** The PUT and DELETE endpoints raised a `404 Not Found` HTTPException on missing entries, whereas the test suite expected a `200 OK` return with a JSON body `{"error": "Entry not found"}`.
- **Action Taken:** Modified both endpoints to return `{"error": "Entry not found"}` with `200 OK` when an entry is not found. This successfully satisfied the REST validation requirements.
- Standardized internal server errors to consistently output structured JSON:
  ```json
  {
    "detail": "Internal server error",
    "request_id": "req-xyz"
  }
  ```

### C. Pagination Consistency
- All bulk listing endpoints support standard query parameters:
  - `limit`: defaults to `50` or `100`, bounded max of `200` or `500`.
  - `offset`: defaults to `0`, validated as non-negative.
- Responses consistently format paginated arrays inside wrapper structures with standard fields:
  ```json
  {
    "orders": [],
    "total": 0,
    "offset": 0,
    "limit": 50
  }
  ```
