"""Automated system verification script.

Verifies route registration compliance, unique route paths, unpinned/pinned dependencies,
no circular imports, and general system health.
"""

import os
import sys
import importlib

# Add repository root to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def verify_routes():
    print("Verifying route registration...")
    from api.main import app

    paths = []
    for route in app.routes:
        if hasattr(route, "path"):
            paths.append(route.path)

    # Check for unique route paths
    duplicates = set([p for p in paths if paths.count(p) > 1])
    if duplicates:
        print(f"FAIL: Duplicate route paths detected: {duplicates}")
        return False

    print(f"PASS: {len(paths)} routes registered successfully with no duplicates.")
    return True


def verify_dependencies():
    print("Verifying pinned dependencies...")
    req_file = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    if not os.path.exists(req_file):
        print("FAIL: requirements.txt not found")
        return False

    unpinned = []
    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" not in line:
                unpinned.append(line)

    if unpinned:
        print(f"FAIL: Unpinned dependencies detected: {unpinned}")
        return False

    print("PASS: All dependencies are explicitly pinned.")
    return True


def verify_imports():
    print("Verifying imports and circular dependencies...")
    try:
        importlib.import_module("api.main")
        importlib.import_module("database")
        importlib.import_module("startup")
        print("PASS: Core modules imported successfully without circular loops.")
        return True
    except Exception as e:
        print(f"FAIL: Module import error: {e}")
        return False


def main():
    print("=== Elite System Verification ===")
    r = verify_routes()
    d = verify_dependencies()
    i = verify_imports()

    if r and d and i:
        print("=== SYSTEM VERIFICATION SUCCESSFUL ===")
        sys.exit(0)
    else:
        print("=== SYSTEM VERIFICATION FAILED ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
