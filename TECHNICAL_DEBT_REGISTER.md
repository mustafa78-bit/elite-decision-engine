# Technical Debt Register: NEXUS (Sprint 15)

This register catalogs, ranks, and prioritizes existing technical debt across the NEXUS codebase. All items are prioritized based on their direct impact on **Founder Trust** and **Operational Reliability**.

---

## 1. Prioritization Matrix

- **P0 (Production Blocker)**: Must be resolved before the very first production deployment.
- **P1 (High Priority)**: Affects usability, analytics fidelity, or developer workflow.
- **P2 (Medium/Low Priority)**: General hygiene, minor optimization, or cosmetic cleanup.

---

## 2. Active Technical Debt Register

### P0 (Production Blockers)

| ID | Issue Description | Severity | Impact | Estimated Effort | Recommended Solution |
|----|-------------------|----------|--------|------------------|----------------------|
| **P0-1** | `ConfidenceEngine` Double-Scaling: Double-scaled to 100 then compared to 0-100 threshold | Critical | Causes all signal evaluations to fall into `STRONG_APPROVE`. | 1 hour | Refactor `core/confidence_engine.py` to prevent redundant multiplier scaling. |
| **P0-2** | `ATRr_14` Typo in indicator column name in indicator engine | Critical | Causes ATR calculations to resolve to default `0` in active market data scans. | 30 mins | Standardize string name lookup to `ATR_14` in `market_data/indicators.py`. |

---

### P1 (High Priority)

| ID | Issue Description | Severity | Impact | Estimated Effort | Recommended Solution |
|----|-------------------|----------|--------|------------------|----------------------|
| **P1-1** | Confidence score hardcoded to 0.0 in DecisionPipeline | High | Breaks threshold classification logic for all executed paper trade pipelines. | 1 hour | Wire the actual output from `ConfidenceEngineV2` into `execution/pipeline.py` instead of the static `0.0` stub. |
| **P1-2** | Raw scores never saved to active Signal records in pipeline | High | Prevents structured audit of historical performance and learning engines. | 2 hours | Map output of `ScoringEngine` into the SQLAlchemy Signal record properties during execution loop writes. |
| **P1-3** | Mixed signal template warnings have no context | High | Warnings list trigger on std-dev but don't state which exact engines are in disagreement. | 1.5 hours | Enhance `ExplainEngine._build_warnings` to specify exactly which dimensions are conflicting. |

---

### P2 (Medium/Low Priority)

| ID | Issue Description | Severity | Impact | Estimated Effort | Recommended Solution |
|----|-------------------|----------|--------|------------------|----------------------|
| **P2-1** | Missing ForeignKey constraints on `Trade.signal_id` | Medium | Risk of orphaned or dangling Trade records on database cascading delete. | 1 hour | Add formal `ForeignKey("signals.id")` constraint to `Trade` schema in `database.py`. |
| **P2-2** | Rate limits set globally rather than per-route scope | Medium | Low-priority endpoints can consume limit capacity from critical execution routes. | 3 hours | Define separate route limit decorators in `api/rate_limit.py` and apply individually. |
| **P2-3** | `datetime.utcnow()` usage in old test packages | Low | Deprecation warnings under Python 3.13/3.14. | 2 hours | Migrate all legacy `utcnow()` instances to standard `datetime.now(timezone.utc)`. |

---

## 3. Summary Scorecard

- **Total Active Issues**: 8
- **P0 Count**: 2 (BP2, BP3 pre-existing codebase artifacts)
- **P1 Count**: 3
- **P2 Count**: 3
- **Action Strategy**: In upcoming Sprint 16, block any feature work until P0 items are closed and verified by the smoke test suite.
