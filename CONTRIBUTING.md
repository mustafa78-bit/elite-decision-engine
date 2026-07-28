# Contributing Guidelines

Thank you for contributing to NEXUS (Elite Decision Engine)! We maintain high engineering standards to preserve Founder Trust as our primary performance metric.

---

## 1. Branching & Pull Requests

- Branch names should be short and descriptive (e.g., `sprint-14-hardening`).
- Keep pull requests focused: one PR should solve exactly one feature or bugfix.
- All code changes must preserve backward compatibility. No architectural expansions are allowed under the Core Architecture Freeze.

---

## 2. Coding Standards

### Python (Backend)
- Standard: **Python >= 3.13**
- Formatter/Linter: `ruff` (Line length 120, target version `py313`).
- **Database Sessions:** Always use `session_scope()` context manager from `database.py` instead of raw session management.
- Keep methods modular, documented, and type-hinted.

### React / TypeScript (Frontend)
- Utilize functional components with React Hooks.
- Do not hardcode values; utilize standard styling variables and classes defined in `tailwind.config.js` or `globals.css`.
- Ensure proper ARIA roles and keyboard accessibility on interactive components.

---

## 3. Testing Requirements

- Every new function or bugfix must be accompanied by comprehensive tests.
- Run the full pytest suite before submitting code:
  ```bash
  poetry run pytest
  ```
- All tests must pass successfully (100% pass rate). Zero flaky or slow tests are tolerated.
- Utilize Playwright integration tests to verify frontend UI changes:
  ```bash
  npx playwright test
  ```

---

Thank you for helping us keep NEXUS clean, fast, and production-ready!
