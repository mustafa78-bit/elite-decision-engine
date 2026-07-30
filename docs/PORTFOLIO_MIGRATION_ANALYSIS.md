# Portfolio Engine Migration Analysis & Safe Migration Plan

This document maps, compares, and structures the migration plan of the duplicated `PortfolioEngine` implementations inside the **Elite Decision Engine** to avoid system regression and establish a single source of truth (SSOT).

---

## 1. Portfolio Engine Usage Map (Usage Map)

### Duplicated Implementations:
1. **Root-Level**: `portfolio_engine.py` (Defines class `PortfolioEngine` and dataclass `PortfolioStats`)
2. **Package-Nested**: `portfolio/engine.py` (Defines class `PortfolioEngine` using nested helper class `PortfolioSnapshot` from `portfolio/core.py`)

### Active Codebase References:

#### Root-Level (`portfolio_engine.py`) Usage Map:
- **`services/terminal_service.py`**:
  ```python
  from portfolio_engine import PortfolioEngine
  ...
  stats = PortfolioEngine().stats()
  ```
- **`api/routes/paper_trading.py`**:
  ```python
  from portfolio_engine import PortfolioEngine
  ```
- **`api/routes/portfolio.py`**:
  ```python
  from portfolio_engine import PortfolioEngine
  ...
  stats = PortfolioEngine().stats()
  ```

#### Package-Nested (`portfolio/engine.py`) Usage Map:
- **`portfolio/__init__.py`**: Exposes package interface.
- **`api/routes/dashboard.py`**:
  ```python
  from portfolio.engine import PortfolioEngine
  ...
  snapshot = PortfolioEngine().snapshot()
  ```
- **`tests/test_performance_engine.py`**:
  ```python
  from portfolio import PortfolioEngine
  ```
- **`tests/test_portfolio_engine.py`**:
  ```python
  from portfolio import PortfolioEngine, PortfolioSnapshot
  ```

---

## 2. Comprehensive Behavior & Interface Comparison

| Characteristic / Metric | Root-Level: `portfolio_engine.py` | Package-Nested: `portfolio/engine.py` |
| :--- | :--- | :--- |
| **Output Data Model** | `PortfolioStats` dataclass (local) | `PortfolioSnapshot` dataclass (from `portfolio/core.py`) |
| **Calculation Source** | Reads exclusively from `Trade` SQLAlchemy model. | Reads from both `Trade` and `PaperTrade` SQLAlchemy models. |
| **Primary Method** | `stats()` -> `PortfolioStats` | `snapshot(current_prices: dict)` -> `PortfolioSnapshot` |
| **Capital Constructor Param** | `initial_equity` (defaults to `ACCOUNT_EQUITY`) | `initial_capital` (defaults to `ACCOUNT_EQUITY`) |
| **Unrealized PnL Calculation** | Hardcoded logic: `sum((t.entry * 0.01) for t in open_trades)` | Realized using paper trade current prices: `delta * pt.quantity` (supports LONG vs SHORT correctly) |
| **Exposure Calculation** | `sum(t.entry for t in open_trades)` | Realized from paper trades: `pt.entry * pt.quantity` |
| **Allocation Calculation** | Computes absolute allocation: `dict[str, float]` | No local dictionary allocation output (handled upstream) |
| **Realized PnL Calculation** | Simple sum of closed trade PnL. | Sum of closed paper trades scaled by unit quantity. |
| **Equity Curve Base** | Uses sequential trade `t.pnl` directly. | Sequentially adjusts by closed paper trade size (`pt.pnl * pt.quantity`). |

### Logic/Behavioral Differences Detail:
1. **Unrealized PnL**:
   - `portfolio_engine.py` uses a crude heuristic: `0.01 * t.entry`.
   - `portfolio/engine.py` maps the exact price delta between the current price index and the entry price for open positions, considering direction (reverses delta on SHORT).
2. **Exposure & Cash**:
   - `portfolio/engine.py` computes detailed multi-direction exposure (total, long, short) and determines remaining cash (`total_equity - exposure`).
   - `portfolio_engine.py` simply sums entry prices for open trades as open exposure, lacking directional exposure split or cash calculations.
3. **Data Dependency Layer**:
   - `portfolio_engine.py` works on standard trades.
   - `portfolio/engine.py` matches trades with corresponding paper trading transactions (`PaperTrade` table) for granular scaling and size multiplications.

---

## 3. Impact Assessment of Root-Level Removal

If `portfolio_engine.py` is immediately removed without structural adjustments, the following modules will instantly fail:

1. **`services/terminal_service.py`**
   - **Failure**: `ImportError: cannot import name 'PortfolioEngine' from 'portfolio_engine'`
   - **Reason**: Tries to import root-level module and execute `stats()`.
2. **`api/routes/paper_trading.py`**
   - **Failure**: `ImportError` on loading module.
3. **`api/routes/portfolio.py`**
   - **Failure**: Route endpoint `/portfolio` will crash as it directly imports from `portfolio_engine` and expects `stats()` attributes.

---

## 4. Safe, Zero-Downtime Migration Plan

To clean up duplicate implementations without causing system downtime or regression:

### Step 1: Interface Expansion on `portfolio/engine.py`
We will augment `portfolio/engine.py`'s `PortfolioEngine` class to dynamically support a compatibility layer.
- Add a compatibility method `.stats()` inside the SSOT `PortfolioEngine` class in `portfolio/engine.py`.
- This `.stats()` method will internally invoke `.snapshot()` and map the fields to a return instance of a compatible `PortfolioStats` structure, preventing breakage in existing modules.

### Step 2: Redirect Imports
Iteratively redirect references from `portfolio_engine.py` to `portfolio.engine` inside the following files:
1. `services/terminal_service.py`
2. `api/routes/paper_trading.py`
3. `api/routes/portfolio.py`

### Step 3: Deprecate & Delete Root-Level Engine
Once all tests and endpoints are fully modified to point to the nested single source of truth package, delete the root-level `portfolio_engine.py` artifact.

### Step 4: Verification Runs
Validate full compilation, linting, and regression coverage by executing the test suite:
```bash
python -m pytest tests/test_portfolio_engine.py
```
