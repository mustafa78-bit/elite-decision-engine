# Sprint 30 — REST API Layer

## Objective

Add a REST API layer to expose Elite Decision Engine functionality externally.

The API reuses existing engine components and does not duplicate business logic.

---

## Added

### API Module

Created:

```text
api/
├── __init__.py
├── main.py
├── routes/
│   ├── __init__.py
│   ├── health.py
│   ├── portfolio.py
│   ├── trades.py
│   ├── performance.py
│   └── control.py
└── schemas.py
