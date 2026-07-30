# Chapter 15: Portfolio Engine

## 📊 Portfolio Performance Analytics
The **Portfolio Engine**, structured under `portfolio/` and `portfolio_engine.py`, processes transactional data (trades, orders, balances) to calculate aggregate portfolio performance and risk metrics.

These metrics are queried by the UI to populate the interactive portfolio dashboard (`Portfolio.tsx`) and the high-density HUD metrics layout (`PortfolioSummaryWidget.tsx`).

---

## 📈 Portfolio Calculation Engine Specifications
The engine calculates a suite of standard financial performance and risk metrics:

### 1. Sharpe Ratio Calculation
Evaluates the risk-adjusted return of the portfolio relative to volatility.
- **Formula**:
  $$\text{Sharpe} = \frac{\bar{R}_p - R_f}{\sigma_p}$$
  Where $\bar{R}_p$ is the annualized mean portfolio return, $R_f$ is the risk-free rate of return (default: `0.02`), and $\sigma_p$ is the annualized standard deviation of daily returns.

### 2. Sortino Ratio Calculation
Evaluates risk-adjusted returns by focusing purely on downside volatility.
- **Formula**:
  $$\text{Sortino} = \frac{\bar{R}_p - R_f}{\sigma_{down}}$$
  Where $\sigma_{down}$ is the standard deviation of negative asset returns (downside risk), protecting the system from penalizing upside volatility.

### 3. Calmar Ratio Calculation
Measures risk-adjusted returns relative to drawdown severity.
- **Formula**:
  $$\text{Calmar} = \frac{\text{Annualized Return}}{\text{Maximum Drawdown}}$$
  Provides a critical safety metric for fund managers by highlighting the return generated relative to historical worst-case drawdowns.

### 4. Maximum Drawdown (MDD) Tracking
Tracks the peak-to-trough decline of portfolio equity over time.
- **Formula**:
  $$\text{MDD} = \max \left( \frac{\text{Peak Value} - \text{Trough Value}}{\text{Peak Value}} \right)$$

### 5. Win Rate & Profit Factor
- **Win Rate**: The ratio of winning trades to total closed trades.
- **Profit Factor**: The ratio of gross profits to gross losses:
  $$\text{Profit Factor} = \frac{\sum \text{Gross Profits}}{\sum \text{Gross Losses}}$$
  A profit factor above `1.0` indicates a profitable system, while a value above `2.0` is considered highly robust.

---

## 🔌 Decoupled API Integration Model
To prevent database locking issues during intensive simulation loops, the Portfolio Engine is fully decoupled from active database connections.

It queries records via read-only transactions, processes calculations in-memory, and exposes metrics via standard data structures. This prevents any risk of `DetachedInstanceError` when lazy-loading database fields over WebSockets or API routes.
