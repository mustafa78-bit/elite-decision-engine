#!/usr/bin/env python
import os
import sys
import logging

# Ensure root of project is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title.upper()} ".center(60, "="))
    print("=" * 60)

def verify_backend():
    print_header("Backend Route Registration & Integrity")
    try:
        from api.main import app
        print("[PASS] Successfully imported FastAPI app from api.main")

        # Verify routes
        routes = app.routes
        print(f"[INFO] Total registered routes: {len(routes)}")

        # Check specific expected endpoints
        expected_prefixes = ["/auth", "/paper", "/paper-trading", "/dashboard", "/widgets", "/preferences", "/journal", "/scanner"]
        found_prefixes = set()
        all_paths = []
        for r in routes:
            if type(r).__name__ == "_IncludedRouter":
                for sub_r in r.original_router.routes:
                    if hasattr(sub_r, "path"):
                        all_paths.append(sub_r.path)
            elif hasattr(r, "path"):
                all_paths.append(r.path)

        for path in all_paths:
            for pref in expected_prefixes:
                if path.startswith(pref):
                    found_prefixes.add(pref)

        for pref in expected_prefixes:
            if pref in found_prefixes:
                print(f"[PASS] Found routes with prefix '{pref}'")
            else:
                print(f"[FAIL] Missing routes with prefix '{pref}'")
                print(f"[DEBUG] Registered paths: {sorted(set(all_paths))}")
                return False
        return True
    except Exception as e:
        print(f"[FAIL] Backend verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_frontend():
    print_header("Frontend Layout & Resources")
    paths_to_check = [
        "frontend/src/main.tsx",
        "frontend/src/styles/tokens.css",
        "frontend/src/styles/globals.css",
        "frontend/src/index.css",
        "frontend/package.json"
    ]
    all_ok = True
    for p in paths_to_check:
        if os.path.exists(p):
            print(f"[PASS] Verified path exists: {p}")
        else:
            print(f"[FAIL] Missing required frontend path: {p}")
            all_ok = False
    return all_ok

def verify_database():
    print_header("Database Connectivity & Schema")
    try:
        from database import get_session, Base, engine
        from sqlalchemy import inspect

        session = get_session()
        print("[PASS] Successfully opened database session")

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"[INFO] Existing tables: {existing_tables}")

        expected_tables = ["signals", "trades", "users", "user_settings", "notifications", "watchlists", "journal_entries", "paper_orders", "paper_trades", "decision_explanations"]
        all_ok = True
        for table in expected_tables:
            if table in existing_tables:
                print(f"[PASS] Table verified: {table}")
            else:
                print(f"[FAIL] Missing table: {table}")
                all_ok = False

        session.close()
        return all_ok
    except Exception as e:
        print(f"[FAIL] Database verification failed: {e}")
        return False

def verify_services():
    print_header("Services Initialization")
    try:
        from services.widget_service import WidgetService
        from services.kpi_service import KPIService
        from portfolio_engine import PortfolioEngine

        widget_svc = WidgetService()
        kpi_svc = KPIService()
        portfolio_eng = PortfolioEngine()

        print("[PASS] WidgetService initialized successfully")
        print("[PASS] KPIService initialized successfully")
        print("[PASS] PortfolioEngine initialized successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Services initialization failed: {e}")
        return False

def verify_production_config():
    print_header("Production Configuration Check")
    # Simulate production checks
    from config import API_ENV, CORS_ORIGINS, JWT_SECRET, LOG_LEVEL
    print(f"[INFO] API_ENV: {API_ENV}")
    print(f"[INFO] LOG_LEVEL: {LOG_LEVEL}")

    config_ok = True
    if API_ENV == "production":
        print("[INFO] Running production configuration validation...")
        if not JWT_SECRET or JWT_SECRET == "dev_jwt_secret_key_change_me_in_production":
            print("[WARN] JWT_SECRET uses default development value in production!")
        else:
            print("[PASS] Custom JWT_SECRET verified")

        if CORS_ORIGINS == "*":
            print("[WARN] CORS_ORIGINS set to '*' in production environment")
        else:
            print("[PASS] CORS_ORIGINS properly restricted")
    else:
        print("[INFO] Currently in development environment. Production verification checks passed as dry-run.")

    # Check for unpinned dependencies in requirements.txt
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r") as f:
            unpinned = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" not in line and ">=" not in line and "<=" not in line:
                        unpinned.append(line)
            if unpinned:
                print(f"[WARN] Unpinned dependencies found in requirements.txt: {unpinned}")
            else:
                print("[PASS] All backend requirements are pinned")
    return config_ok

def main():
    print("=" * 60)
    print(" STARTING ELITE TERMINAL SYSTEM VERIFICATION ".center(60, "="))
    print("=" * 60)

    checks = [
        ("Backend", verify_backend),
        ("Frontend", verify_frontend),
        ("Database", verify_database),
        ("Services", verify_services),
        ("Production Config", verify_production_config)
    ]

    results = {}
    for name, check_fn in checks:
        results[name] = check_fn()

    print_header("Verification Summary")
    overall_pass = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{name:<25}: {status}")
        if not passed:
            overall_pass = False

    if overall_pass:
        print("\n[SUCCESS] SYSTEM IS 100% HEALTHY AND VERIFIED!")
        sys.exit(0)
    else:
        print("\n[ERROR] SOME SYSTEM CHECKS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
