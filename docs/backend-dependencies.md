# Backend Dependency Report

## Module Dependency Graph

```
api/
├── app.py         → core.engine, core.health, api.routes, api.websocket, api.schemas
├── routes.py      → api.schemas, api.errors, core.engine, core.health
├── schemas.py     → (standalone, dataclasses)
├── errors.py      → (standalone)
├── middleware.py  → api.errors, api.schemas
├── websocket.py   → (standalone, dataclasses)
└── __init__.py    → Re-exports from schemas, errors, middleware, websocket, app

core/
├── engine.py      → database, config, core.intelligence, decision.models
├── intelligence.py → filters.btc_filter, decision.fusion
├── health.py      → api.schemas
├── dashboard.py   → core.engine, core.health, core.cache, dto.models, decision.trade_memory
├── cache.py       → (standalone)
├── retry.py       → (standalone)
├── scheduler.py   → (standalone)
├── validation.py  → (standalone, os)
├── serialization.py → (standalone)
└── __init__.py    → Re-exports from all core modules

dto/
├── models.py      → core.serialization
└── __init__.py    → Re-exports

decision/
├── engine.py      → database, scoring.engine, decision.models, decision.confidence
├── models.py      → (standalone, dataclasses)
├── confidence.py  → decision.models
├── fusion.py      → (standalone)
└── trade_memory.py → decision.models

modules/ (whale, liquidity, orderflow, market_structure, news, sentiment, macro)
└── Each: models.py → analyzer.py → integration.py → __init__.py
```

## External Dependencies

| Package | Used By | Purpose |
|---------|---------|---------|
| sqlalchemy | database.py, decision/engine.py | ORM for PostgreSQL |
| psycopg2-binary | database.py | PostgreSQL driver |
| python-dotenv | config.py | .env file loading |
| requests | News/sentiment modules | HTTP requests |
| pytest | All tests | Test framework |

## Circular Dependency Check

No circular dependencies detected. The dependency graph is acyclic:
- `api/` → `core/` → `decision/` → `modules/` (one-way)
- `core/serialization.py` has no dependencies (leaf node)
- `api/__init__.py` only re-exports (no import cycles)
