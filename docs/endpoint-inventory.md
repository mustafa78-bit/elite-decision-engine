# Endpoint Inventory

| # | Path | Method | Service | Backend | Frontend |
|---|------|--------|---------|---------|----------|
| 1 | `/health` | GET | `DecisionRouter.get_health()` | ✅ | ✅ |
| 2 | `/ready` | GET | `DecisionRouter.get_readiness()` | ✅ | ✅ |
| 3 | `/live` | GET | `DecisionRouter.get_liveness()` | ✅ | ✅ |
| 4 | `/metrics` | GET | `DecisionRouter.get_metrics()` | ✅ | ✅ |
| 5 | `/decisions` | GET | `DecisionRouter.get_decisions()` | ✅ | ✅ |
| 6 | `/decisions/:id` | GET | `DecisionRouter.get_decision_by_id()` | ✅ | ✅ |
| 7 | `/intelligence` | GET | `DecisionRouter.get_intelligence()` | ✅ | ✅ |
| 8 | `/features` | GET | `DecisionRouter.get_features()` | ✅ | ✅ |
| 9 | `/modules` | GET | `DecisionRouter.get_modules()` | ✅ | ✅ |
| 10 | `/app` | GET | `APIApp.get_app_info()` | ✅ | 🔲 |
