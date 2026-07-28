# NEXUS Founder Alpha — Developer Onboarding Guide

Welcome to **NEXUS**, the ultimate Executive Decision Operating System for professional founders. This guide is designed to get any skilled engineer fully oriented, set up, and ready to contribute to NEXUS in under one hour.

---

## 1. Introduction & Mission

NEXUS is not a standard trading bot or market dashboard. It is a **Unified Decision Kernel** built to reduce a Founder's cognitive load. It addresses the central question:
> *"Will this help the Founder make a better decision today?"*

NEXUS acts as the Founder's AI Chief of Staff (OLLO OS), running quantitative discovery, checking trust calibration, managing paper trade simulation, and tracking journal post-mortems with military-grade explainability.

---

## 2. Core Architecture Overview

NEXUS uses a highly structured, decoupled, and event-driven architecture divided into key functional components:

```
                      ┌────────────────────────┐
                      │    Founder Frontend    │
                      │  (React, Vite, Tailwind)│
                      └───────────┬────────────┘
                                  │ JSON API / WebSockets
                                  ▼
                      ┌────────────────────────┐
                      │     FastAPI Gateway     │
                      │       (api/main.py)    │
                      └───────────┬────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│     OLLO OS     │      │ Decision Kernel │      │Discovery Engine │
│(services/ollo/os)│     │(decision/kernel)│      │(services/disco) │
└─────────────────┘      └────────┬────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Event Ledger  │
                         │ (EventLedger DB)│
                         └─────────────────┘
```

### The 12-Stage Cognitive Kernel
Every single decision evaluated by NEXUS runs through a deterministic 12-stage cognitive pipeline:
1. **Observe:** Feed raw live tick, volume, and order-book inputs.
2. **Understand:** Construct structured indicator contexts.
3. **Connect:** Link signals with the L2 Relationship Graph.
4. **Reason:** Multi-advisor AI Council analysis.
5. **Evaluate:** Enforce systemic risk parameters.
6. **Trust:** Compute expected calibration and trust scores.
7. **Learn:** Query pattern database for historical analogues.
8. **Calibrate:** Match prediction confidence to mathematical Win/Loss expectations.
9. **Decide:** Final execute, hold, or cancel determination.
10. **Explain:** Ground decisions with multi-factor proof markers.
11. **Remember:** Append to permanent memory and Knowledge Graph.
12. **Improve:** Log self-calibration feedback loop.

### Core Data Models (`database.py`)
- **Signal:** Market conditions, multi-factor scoring metrics, and AI recommendations.
- **Trade:** Active, open, and closed execution states.
- **JournalEntry:** Qualitative and emotional state context linking to execution.
- **PaperOrder & PaperTrade:** Parallel high-fidelity paper simulation tracking.
- **DecisionExplanation:** High-density, multi-layer grounded explanations.

---

## 3. Local Development Environment Setup

NEXUS requires **Python >= 3.13** and **Node.js >= 18**.

### Backend Setup (Python 3.13)
1. Ensure pyenv has Python 3.13.2 installed and set as global:
   ```bash
   pyenv install 3.13.2
   pyenv global 3.13.2
   ```
2. Configure poetry env and install all requirements:
   ```bash
   poetry env use 3.13.2
   poetry install --no-root
   ```
3. Initialize SQLite local database and seed data:
   ```bash
   poetry run python seed_data.py
   ```
4. Start the FastAPI API Server:
   ```bash
   poetry run uvicorn api.main:app --reload --port 8000
   ```

### Frontend Setup (React, Vite)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```

---

## 4. Run & Validate the Project

To ensure full system health, always run the validation toolkit with one command:

### Run Complete Backend Test Suite
```bash
poetry run pytest
```
*Note: Over 1320 tests validate everything from signal processing, AI Council rating, pattern recognition, graph calculations, up to FastAPI E2E endpoints.*

### Run Frontend Playwright Integration Tests
```bash
cd frontend
npx playwright test
```

---

## 5. Coding Principles & Guidelines

### I. Will this help the Founder make a better decision today?
If the code does not reduce cognitive load, verify trust, or directly make decisions more traceable, it does not belong in NEXUS.

### II. Edit Source, Not Artifacts
Do not edit any file in `dist/`, `build/`, or generated static bundles. Locate source codes in `/api`, `/core`, `/decision`, or `frontend/src` and rebuild properly.

### III. Transactional Session Management
Always wrap database operations with `session_scope` from `database.py`:
```python
from database import session_scope

with session_scope() as session:
    # Operations are automatically committed/rolled back here
    session.add(my_model)
```
Do not call raw `session.close()` directly.

---

## 6. Onboarding FAQs & Troubleshooting

- **Why is the database locked?** SQLite does not support highly parallel writes. Ensure no stale uvicorn processes are running using `pkill -f uvicorn`.
- **JWT token validation fails?** Ensure you have `.env` properly populated. Standard default fallback is verified in development.
- **How to override the mock server with live Hyperliquid tick data?** Change `API_ENV` to `development` or `production` and configure your API keys in `.env`.

Welcome to NEXUS! Let's build the future of Founder Intel.
