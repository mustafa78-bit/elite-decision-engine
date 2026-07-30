# Chapter 21: Testing Methodology

## 🧪 Comprehensive Test Suite
The NEXUS platform maintains a comprehensive automated testing suite consisting of over **1,325 unit, integration, and E2E test cases** structured under `tests/`.

The test suite runs on **Python 3.13** and ensures that all core engines, routers, risk guards, and calculators operate reliably across updates.

---

## 🏗️ Test Suite Organization & Target Targets

The test modules are organized logically to match the platform's architectural layers:

```
tests/
  ├── test_api_main.py                 # Core FastAPI router & WS manager checks
  ├── test_auth.py / test_api_auth.py  # JWT generation, whitelisting & login flows
  ├── test_pipeline.py                 # DecisionPipeline data gathering audits
  ├── test_risk_manager.py             # Pre-flight safety validations & rejection codes
  ├── test_tp_sl.py                    # ATR-based entry/stop/profit calculations
  ├── test_trade_engine.py             # Duplicate guards & trade creation logic
  ├── test_paper_executor.py           # Simulated ticking, TP/SL hits, and liquidations
  ├── test_portfolio_engine.py         # Performance metric equations (Sharpe, Sortino, drawdowns)
  ├── test_council_agents.py           # specialized agent personas and debate consensus
  └── test_evidence_engine.py          # Evidence builders & conflict detection triggers
```

---

## ⚡ Mocking Strategies & Isolation
To maintain deterministic testing conditions and prevent external network dependencies, NEXUS isolates tests using robust mocking strategies:
- **`Database Isolation`**: Tests run on an in-memory SQLite configuration (`sqlite:///:memory:`). This avoids state leakage, ensures rapid test runs, and isolates database operations.
- **`FastAPI TestClient`**: Used to simulate API requests and WebSocket handshakes within isolated test sessions.
- **`Mock Exchange Adapters`**: Replaces live Hyperliquid and Binance API connections with predictable mock data objects, allowing connection failures, rate limits, and order executions to be tested deterministically.
- **`Transactional Rollbacks`**: Automatically wraps test transactions in rollbacks to keep the database state clean between tests.
- This comprehensive testing approach maintains high confidence in the core trading logic and prevents regressions across updates.
