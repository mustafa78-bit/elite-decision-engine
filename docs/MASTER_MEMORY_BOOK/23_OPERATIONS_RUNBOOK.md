# Chapter 23: Operations Runbook

## 🛠️ Operations & Maintenance Runbook
This runbook provides step-by-step instructions for deploying, seeding, and troubleshooting the NEXUS platform.

---

## 🚀 Standard Installation & Local Setup

To set up a local development environment:

### 1. Prerequisites
Ensure you have the following installed on your machine:
- Python 3.13 (or newer)
- Poetry
- Node.js (v20 or newer) and npm

### 2. Environment Configuration
Copy the template configuration file and verify your local settings:
```bash
cp .env.example .env
```
Ensure the default configuration variables are set for local development:
- `DATABASE_URL=sqlite:///decision_engine.db`
- `API_ENV=development`
- `JWT_SECRET=your-secret-key-must-be-32-bytes-minimum`

### 3. Backend Dependency Setup
Install backend dependencies and run the server using Poetry:
```bash
poetry env use python3.13
poetry install --no-root
poetry run python -m uvicorn api.main:app --reload --port 8000
```

### 4. Frontend Dependency Setup
In a new terminal window, navigate to the frontend directory, install dependencies, and start the development server:
```bash
cd frontend
npm install
npm run dev
```
Open your browser and navigate to `http://localhost:5173` to access the Command Center HUD.

---

## 💾 Local Seeding & State Simulation
To populate the database with mock signals, simulated trades, user profiles, and journal records for local testing:
```bash
poetry run python startup.py
```
This runs the initialization script, setting up database tables and seeding the database to simulate an active daily trading workflow.

---

## 🩺 System Diagnostics & Troubleshooting

Use these internal diagnostic endpoints and logs to troubleshoot system issues:

### 1. Read-Only Diagnostics Endpoints
- `GET /health`: Returns the health status, active environment, and system uptime.
- `GET /monitoring/engineering`: Exposes system metrics, active WebSocket connections, and room subscriptions.

### 2. Rotating Server Logs
Logs are automatically written to the `logs/` directory using rotating file handlers (maximum **10MB per file**, keeping **5 backups**):
- `logs/engine.log`: Tracks the background ExecutionLoop, signal polls, and evaluation ticks.
- `logs/trade.log`: Logs trade executions, paper positions updates, and TP/SL liquidations.
- `logs/error.log`: Records unhandled errors, stack trace snapshots, and validation failures.

### 3. Quick Recovery Actions
- **Database Reset**: To wipe local SQLite tables and start fresh:
  ```bash
  rm decision_engine.db
  poetry run python startup.py
  ```
- **Port Conflicts**: If the server fails to start due to a "port already in use" error, locate and terminate the conflicting process:
  ```bash
  kill $(lsof -t -i :8000) 2>/dev/null || true
  ```
- **Stuck Simulated Trade**: If an active simulated position becomes stuck due to an exchange adapter issue, update its status manually in the database to clear the execution loop:
  ```sql
  UPDATE trades SET status = 'CLOSED', close_reason = 'MANUAL_OVERRIDE' WHERE status = 'OPEN';
  ```
