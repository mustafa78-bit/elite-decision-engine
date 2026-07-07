# Sprint 28 — Continuous Integration

## Objective

Implement CI for the Elite Decision Engine. Every push and pull request must automatically verify that the project builds and all tests pass.

## Workflow

**File**: `.github/workflows/ci.yml`

**Name**: `CI`

### Triggers

| Event | Branches |
|-------|----------|
| `push` | `main`, `live-execution` |
| `pull_request` | `main`, `live-execution` |

### Python Version

`3.13`

### Steps

```
Checkout repository (actions/checkout@v4)
      │
      ▼
Setup Python 3.13 (actions/setup-python@v5)
  │
  ├── cache: pip
  └── cache-dependency-path: requirements.txt
      │
      ▼
Install dependencies
  │
  ├── pip install --upgrade pip
  └── pip install -r requirements.txt
      │
      ▼
Run tests
  │
  ├── rm -f test_elite.db
  └── python -m pytest tests/ -v --tb=short
      │
      ▼
Fail if any test fails
```

### Caching

Pip packages are cached via `actions/setup-python@v5` using `requirements.txt` as the cache key.

### Badge

Added to README.md:

```
![CI](https://github.com/mustafa78-bit/elite-decision-engine/actions/workflows/ci.yml/badge.svg)
```

## Modified Files

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | **New** — CI workflow (28 lines) |
| `README.md` | Add CI badge after title |

## Tests

No application tests modified. All 266 existing tests pass.

```
$ python -m pytest tests/ --tb=short -q
266 passed, 1 warning in 3.33s
```

## Git Diff

```diff
diff --git a/README.md b/README.md
index 03c7511..54c5bdb 100644
--- a/README.md
+++ b/README.md
@@ -1,5 +1,7 @@
 # Elite Decision Engine
 
+![CI](https://github.com/mustafa78-bit/elite-decision-engine/actions/workflows/ci.yml/badge.svg)
+
 Automated paper trading engine for cryptocurrency markets (Hyperliquid).
```

## Remaining Blockers

None.

## Next Recommendation

**Sprint 29 — CLI Dashboard Command**: Add a `python -m engine live` CLI command that displays open positions, portfolio stats, and performance metrics in a formatted table. Uses existing `PortfolioEngine`, `PerformanceEngine`, and `PaperExecutor` under the hood.
