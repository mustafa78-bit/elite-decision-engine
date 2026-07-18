#!/bin/sh
# =====================================================================
# Elite Decision Engine - Production PostgreSQL Backup Script
# =====================================================================
# This script:
#   1. Backs up the PostgreSQL database using pg_dump.
#   2. Compresses the backup using gzip.
#   3. Rotates local backups (keeps the last 7 days).
#   4. Gracefully synchronizes with S3 if configured.

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="backup_${TIMESTAMP}.sql.gz"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

# Resolve database configuration with robust environment alignment
DB_HOST="${DB_HOST:-$POSTGRES_HOST}"
DB_USER="${DB_USER:-$POSTGRES_USER}"
DB_NAME="${DB_NAME:-$POSTGRES_DB}"
DB_PASSWORD="${DB_PASSWORD:-$POSTGRES_PASSWORD}"

# Fall back to standard defaults if completely empty
DB_HOST="${DB_HOST:-db}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-decision_engine}"

echo "=== [$(date)] Starting Automated Database Backup ==="

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# 1. Execute pg_dump
echo "Dumping database ${DB_NAME} from host ${DB_HOST}..."
PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${FILEPATH}"

echo "Backup written successfully: ${FILEPATH} ($(du -sh "${FILEPATH}" | cut -f1))"

# 2. Local backup rotation (Keep last 7 days / 168 hours)
echo "Running local backup rotation (retention: 7 days)..."
find "${BACKUP_DIR}" -name "backup_*.sql.gz" -type f -mtime +7 -exec rm -f {} \;
echo "Local backup rotation complete."

# 3. AWS S3 Upload (optional)
if [ -n "${S3_BUCKET}" ] && [ -n "${AWS_ACCESS_KEY_ID}" ] && [ -n "${AWS_SECRET_ACCESS_KEY}" ]; then
    echo "AWS S3 credentials detected. Uploading backup to s3://${S3_BUCKET}..."
    if aws s3 cp "${FILEPATH}" "s3://${S3_BUCKET}/db_backups/${FILENAME}"; then
        echo "Successfully uploaded backup to S3."
    else
        echo "WARNING: AWS S3 upload failed, but local backup remains intact."
    fi
else
    echo "AWS S3 upload skipped (credentials or S3_BUCKET not fully set)."
fi

echo "=== [$(date)] Backup Process Completed Successfully ==="
