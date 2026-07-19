# Release and Deployment Checklists

---

## 1. Release Checklist (v1.0.0-rc1)

This checklist covers pre-release and coordination steps required prior to initiating deployment.

- [ ] **Code Freeze**: No new commits permitted on the release branch except critical hotfixes.
- [ ] **Linter & Code Quality**:
  - Run backend code audit and verify zero syntax issues.
  - Run frontend audit: `npm run lint --prefix frontend` (oxlint).
- [ ] **Backend Test Suite Validation**:
  - Run all pytest suites: `poetry run pytest`.
  - Confirm all **1,325 tests** pass with 100% success rate.
- [ ] **Frontend Test Suite Validation**:
  - Run all Vitest suites: `npm --prefix frontend test -- --run`.
  - Confirm all **106 tests** pass successfully.
- [ ] **Production Compiler Sanity**:
  - Run strict Type-Checking: `npx tsc -b frontend/tsconfig.json`.
  - Run production compilation: `npm run build --prefix frontend`.
  - Verify zero compilation/bundler errors.
- [ ] **Secrets Verification**:
  - Check that no development passwords, secrets, or keys are committed to the codebase.
  - Verify that `logging_config.py` filters sensitive variables.
- [ ] **Git Tagging**:
  - Create annotated Git tag: `git tag -a v1.0.0-rc1 -m "Founder Alpha Release Candidate 1"`.

---

## 2. Deployment Checklist

This checklist describes the steps for deploying the Release Candidate to the staging/production environments.

### Phase A: Pre-Flight Env Check
- [ ] Verify Docker daemon is active: `docker info`.
- [ ] Check environment variables file is provisioned: `.env` based on `.env.example`.
- [ ] Validate critical secrets:
  - `JWT_SECRET` must be set and must be at least 32 characters.
  - `API_ENV` must be set to `production`.
  - `CORS_ORIGINS` must not be a wildcard (`*`).
- [ ] Ensure directories exist and have correct permissions:
  - `./logs`
  - `./backups`

### Phase B: Backup & Database Check
- [ ] Perform a pre-deployment database backup:
  - Run `./scripts/backup.sh` to capture the current state of SQLite/PostgreSQL.
- [ ] Confirm backing up files are readable and have positive file sizes.

### Phase C: Build & Launch
- [ ] Clean build and start services using Docker Compose:
  - `docker compose -f docker-compose.prod.yml up --build -d`
- [ ] Monitor logs during startup:
  - `docker compose -f docker-compose.prod.yml logs -f --tail=100`
- [ ] Check service status and health check:
  - Verify port 8000 (backend API) returns 200 OK: `curl http://localhost:8000/health`.
  - Verify port 3000 (frontend server) is serving properly.

---

## 3. Rollback Checklist

If a production-impacting incident occurs during or immediately after deployment, follow these instructions to return to a safe state.

- [ ] **Stop Current Services**:
  - Halt the faulty release containers: `docker compose -f docker-compose.prod.yml down`.
- [ ] **Rollback Codebase State**:
  - Reset repository to the previous stable release tag: `git checkout v0.9.5-beta` (or previous stable tag).
- [ ] **Restore Database State**:
  - If schema migrations took place and data integrity is compromised, restore the pre-deployment database dump:
  - Run database restoration script (e.g. `pg_restore` or copying SQLite file back).
- [ ] **Rebuild & Relaunch Stable Containers**:
  - Recompile and relaunch previously stable containers: `docker compose -f docker-compose.prod.yml up --build -d`.
- [ ] **Verify Service Recovery**:
  - Query health checks: `curl http://localhost:8000/health`.
  - Audit logs for recovery confirmation.

---

## 4. Known Limitations & Technical Debt

The following limitations are known and will be addressed in future production releases:

1. **SQLite Concurrent Writes**: Under extremely high simulated tick frequencies, SQLite (the default dev database) may experience transient connection blocks. For high-volume production deployments, PostgreSQL is strictly required.
2. **Synthetic Data Realism**: Although synthetic playback modes (Capitulation, Bull Run) provide high-fidelity feeds, they do not perfectly simulate unexpected external geopolitical news events.
3. **Mock WebSocket Clients**: In constrained testing sandboxes, WebSocket counts reflect local clients and are not dynamically clustered across multi-node server scaling.
