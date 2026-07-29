# NEXUS FOUNDER BETA RELEASE ENGINEER SUMMARY (SPRINT 18)

## 1. Version Mapping & Release Artifacts
*   **Release Version Tag**: `v1.0.0-beta.0`
*   **Git Branch**: `release/founder-beta`
*   **Build Target**: `production-ready` Decision Kernel
*   **Requires Python**: `>=3.13.1`
*   **Database Engine**: SQLAlchemy with PostgreSQL 16 (production) or SQLite (testing)

---

## 2. Release & Rollback Playbook

### Safe Deployment Plan:
1.  **Stop Periodic Workers**: Stop background engine loop and scheduler processes.
2.  **Database Migration**: Run migration scripts to verify constraints.
3.  **Application Startup**: Boot API server and check startup indicators.
4.  **Verification**: Execute `./founder_beta_check.sh` on target server.

### Backup Strategy:
*   Before deploying, run manual PostgreSQL dumps:
    `pg_dump -U postgres -h localhost -d decision_engine -F c -b -v -f "nexus_backup_$(date +%F).dump"`
*   Verify backup dump existence and size prior to halting workers.

### Rollback Playbook:
If post-deployment smoke tests fail or uvicorn logs report errors:
1.  **Terminate Active Server**: `kill $(lsof -t -i :8000) 2>/dev/null || true`
2.  **Restore DB Backup**: Restore previous PG state:
    `pg_restore -U postgres -h localhost -d decision_engine --clean nexus_backup_XXXX.dump`
3.  **Checkout Previous Tag**: `git checkout v0.9.0`
4.  **Restart Server**: Start stable server version in production mode.
