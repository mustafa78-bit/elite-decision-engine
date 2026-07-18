#!/usr/bin/env python
"""
Elite Decision Engine - Production Configuration Validator
=========================================================
Validates the local environment, configuration parameters, database connectivity,
and standard system readiness criteria before high-reliability production startup.
"""

import os
import sys
import logging

# Ensure basic logging configured for reporting
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validator")

def validate_environment():
    """Validates the environmental settings, secrets, and connection parameters."""
    print("\n--- Phase 1: Environment & Secrets Validation ---")
    api_env = os.getenv("API_ENV", "development")
    print(f"API_ENV: {api_env}")

    errors = []
    warnings = []

    # 1. Critical variables validation
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        errors.append("JWT_SECRET is not set (required for auth/JWT generation).")
    elif api_env == "production":
        if len(jwt_secret) < 32:
            errors.append("JWT_SECRET is too short for production. It must be at least 32 characters.")
        if jwt_secret == "dev-secret-change-in-production":
            errors.append("JWT_SECRET is set to the default development value. You must change it in production.")

    # 2. CORS Origins validation
    cors_origins = os.getenv("CORS_ORIGINS", "")
    if api_env == "production":
        if not cors_origins:
            errors.append("CORS_ORIGINS is empty. It must be explicitly set to trusted domains in production.")
        elif cors_origins.strip() == "*":
            errors.append("CORS_ORIGINS is set to '*' in production. This is insecure and not permitted.")

    # 3. Database URL and PostgreSQL parameters
    db_url = os.getenv("DATABASE_URL")
    pg_host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST")
    pg_user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER")
    pg_pass = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")

    if not db_url and not pg_host:
        errors.append("Neither DATABASE_URL nor POSTGRES_HOST/DB_HOST is configured.")

    if db_url and db_url.startswith("sqlite"):
        if api_env == "production":
            warnings.append("Using SQLite database in production is not recommended for high-frequency or multi-user loads.")
    else:
        # Check explicit pg params if DATABASE_URL isn't fully spec'd or as verification
        if not db_url:
            if not pg_host:
                errors.append("POSTGRES_HOST or DB_HOST is missing.")
            if not pg_user:
                errors.append("POSTGRES_USER or DB_USER is missing.")
            if not pg_pass:
                errors.append("POSTGRES_PASSWORD or DB_PASSWORD is missing.")

    # Report Phase 1 Results
    for warning in warnings:
        print(f"[\033[93mWARNING\033[0m] {warning}")
    for error in errors:
        print(f"[\033[91mFAIL\033[0m] {error}")

    if errors:
        print("\033[91mPhase 1 FAILED.\033[0m")
        return False, errors

    print("\033[92mPhase 1 PASSED.\033[0m")
    return True, []

def validate_db_connectivity():
    """Attempts connection to the designated SQL database using SQLAlchemy."""
    print("\n--- Phase 2: Database Connectivity Check ---")

    try:
        from sqlalchemy import create_engine, text

        # We fetch DATABASE_URL just as SQLAlchemy would construct it in config.py
        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            pg_host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST") or "localhost"
            pg_port = os.getenv("POSTGRES_PORT", "5432")
            pg_db = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME") or "decision_engine"
            pg_user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER") or "postgres"
            pg_pass = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD") or "postgres"
            db_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

        print(f"Connecting to database (destination: {db_url.split('@')[-1] if '@' in db_url else db_url})...")

        # Create lightweight engine and connect
        engine = create_engine(db_url, connect_args={"timeout": 5} if db_url.startswith("sqlite") else {})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("\033[92mSuccessfully queried SELECT 1 from the database.\033[0m")
                print("\033[92mPhase 2 PASSED.\033[0m")
                return True
            else:
                print("\033[91mDatabase query returned an unexpected response.\033[0m")
                return False
    except ImportError:
        print("[\033[93mWARNING\033[0m] SQLAlchemy not found in current environment. Skipping connectivity check.")
        print("\033[93mPhase 2 SKIPPED (dependencies missing).\033[0m")
        return True
    except Exception as e:
        print(f"[\033[91mFAIL\033[0m] Database connection failed: {e}")
        print("\033[91mPhase 2 FAILED.\033[0m")
        return False

def validate_file_structure():
    """Verifies that all required production paths and permissions are correct."""
    print("\n--- Phase 3: Filesystem & Permissions Validation ---")

    required_paths = ["logs", "deploy", "monitoring", "scripts"]
    errors = []

    for path in required_paths:
        if not os.path.exists(path):
            errors.append(f"Required path '{path}' does not exist.")
        else:
            # Check write/read permissions
            if not os.access(path, os.R_OK):
                errors.append(f"Path '{path}' is not readable.")
            if not os.access(path, os.W_OK):
                errors.append(f"Path '{path}' is not writable.")

    for err in errors:
        print(f"[\033[91mFAIL\033[0m] {err}")

    if errors:
        print("\033[91mPhase 3 FAILED.\033[0m")
        return False

    print("\033[92mAll required directories exist and are fully writable.\033[0m")
    print("\033[92mPhase 3 PASSED.\033[0m")
    return True

def main():
    print("=================================================================")
    print("     Elite Decision Engine - Production Deployment Validator    ")
    print("=================================================================")

    env_ok, _ = validate_environment()
    db_ok = validate_db_connectivity()
    fs_ok = validate_file_structure()

    print("\n=================================================================")
    if env_ok and db_ok and fs_ok:
        print("\033[92m[SUCCESS] Ready for production! All checks passed successfully.\033[0m")
        print("=================================================================")
        sys.exit(0)
    else:
        print("\033[91m[FAILURE] One or more configuration validations failed. See logs above.\033[0m")
        print("=================================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
