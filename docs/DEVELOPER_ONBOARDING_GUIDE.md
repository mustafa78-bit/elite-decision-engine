# 🚀 NEXUS Developer Onboarding Guide

Welcome to the **NEXUS Decision Operating System** engineering team! This comprehensive guide is designed to get you fully onboarded, set up, and verifying code within one hour.

---

## 1. Stack & Environment Requirements

NEXUS runs on a split architecture consisting of an AI-powered Python backend and a React (Vite) typescript frontend.

### Prerequisites

1. **Python >= 3.13** (Strict requirement specified in `pyproject.toml`).
2. **Poetry** (For backend dependency & virtual environment management).
3. **Node.js >= 20** and **npm** (For the frontend React suite).

---

## 2. Backend Setup & Configuration

### Local Installation

Follow these steps to configure your Python environment and download backend dependencies:

```bash
# 1. Ensure you are using Python 3.13 via pyenv
pyenv global 3.13.2

# 2. Tell Poetry to use Python 3.13
poetry env use 3.13.2

# 3. Install packages without installing the package as root
poetry install --no-root
```

### Configuration & Environment Variables

All parameters are configured via environment variables or a `.env` file in the root directory. Copy the `.env.example` as your starting point:

```bash
cp .env.example .env
```

Key environment parameters:

| Variable | Default Value | Purpose |
|----------|---------------|---------|
| `DATABASE_URL` | `sqlite:///elite.db` | Production and runtime DB URL |
| `TEST_DATABASE_URL` | `sqlite:///test_elite.db` | Test database path |
| `API_ENV` | `development` | Environment target (`production` / `development` / `test`) |
| `JWT_SECRET` | *(required in prod)* | Secret used to sign and decode user tokens |
| `CORS_ORIGINS` | `*` *(development)* | CORS allow-list |

---

## 3. Under-the-Hood Cognitive Architecture

The core of NEXUS operates as an append-only event-driven Decision Kernel. Every incoming signal flows sequentially through the following pipeline phases:

```
                    ┌──────────────┐
                    │  Trading     │
                    │  Signal      │
                    │  (DB: OPEN)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Decision    │
                    │  Engine      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Decision    │
                    │  Pipeline    │
                    │  (filter +   │
                    │   score +    │
                    │   conf)      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Risk        │
                    │  (5 rules)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Position    │
                    │  Sizing      │
                    │  (ATR-based) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Trade       │
                    │  (TP/SL)     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Trade       │
                    │  (DB: OPEN)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Paper       │
                    │  Executor    │
                    │  (monitor    │
                    │   TP/SL)     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Trade       │
                    │  (DB: CLOSED)│
                    └──────────────┘
```

### Core Architecture Components

1. **Signals**: Generated indicators of divergence, candle breakouts, or market momentum (`Signal` table).
2. **Decision Engine & Pipeline**: Scores signals and determines absolute confidence dynamically. Approves signals with a score exceeding `MIN_SCORE` (default `85`).
3. **Risk Manager**: Evaluates the signal against 5 strict risk parameters:
   - Max concurrent open trades check.
   - Per-symbol exposure bounds check.
   - Cumulative portfolio exposure bounds check.
   - Position-size limit constraint check.
   - Cumulative daily drawdown and loss check.
4. **Position Sizing**: Dynamically calculates the quantity using Average True Range (ATR) metrics and risk per trade values.
5. **Trade Engine**: Commits approved executions to the database. Sets stop-loss (SL) and take-profit (TP) levels.
6. **Paper Executor**: Continuously monitors the active trades and automatically closes them when stop-loss or take-profit price bounds are triggered.

---

## 4. Frontend Setup & Build

NEXUS includes a state-of-the-art dark-themed React HUD with a Bloomberg-style Terminal.

To start the local developer workspace:

```bash
cd frontend

# Install packages
npm install

# Start local server
npm run dev

# Build the frontend artifacts
npm run build
```

---

## 5. Test Suite & Verification

The project enforces high test coverage with a comprehensive suite of unit and integration tests.

### Running Backend Tests

Run the full pytest suite:

```bash
poetry run pytest
```

Alternatively, you can utilize our **custom test summary tool** which filters warnings and formats results concisely:

```bash
python3 /home/jules/self_created_tools/run_tests.py
```

### Running Frontend Tests

Execute the frontend unit test suite:

```bash
cd frontend
npm run test
```

---

## 6. Maintenance & Best Practices

- **Transactional Scopes**: Always wrap database writes in the `session_scope()` context manager to guarantee proper connection closing, automatic commit, and rollback on failure.
- **Null Safety**: All overview page metrics must render with robust null checks to prevent runtime dashboard crashes when zero trading data exists.
- **REST Protocol Standards**: Handle API queries dynamically by always wrapping endpoint parameter lists with `**kwargs` inside service functions. This prevents routing errors when clients supply unused search criteria.

---

*Welcome to the NEXUS core team! Reach out on our Discord channel if you have any questions.*
