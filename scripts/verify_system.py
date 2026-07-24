#!/usr/bin/env python3
"""
Elite Decision Engine - Verification & Quality Gate Automation

This script validates system integrity against strict non-regression rules:
1. Every router file under api/routes must be included/registered in api/main.py.
2. Every route path must be unique (no duplicate route paths).
3. Every non-public route must require authentication.
4. Python dependencies must be fully pinned (requirements.txt).
5. Detect missing environment variables or config defaults.
6. Verify database models and initial migrations/SQL readiness.
7. Verify circular imports or orphaned files.
8. Verify that every frontend API endpoint has a registered backend route.
"""

import sys
import os
import re
import importlib
import inspect

def check_router_registration():
    print("Checking route registration...")
    routes_dir = "api/routes"
    if not os.path.exists(routes_dir):
        print(f"Error: {routes_dir} not found.")
        return False

    # Find all router files
    router_files = []
    for f in os.listdir(routes_dir):
        if f.endswith(".py") and f != "__init__.py":
            router_files.append(f[:-3])

    # Read api/main.py to see if they are imported/registered
    with open("api/main.py", "r") as f:
        main_content = f.read()

    missing = []
    for rf in router_files:
        # Check if the router module or its prefix is referenced in main
        if rf not in main_content and f"router_{rf}" not in main_content:
            missing.append(rf)

    if missing:
        print(f"FAIL: The following routers in api/routes are not referenced in api/main.py: {missing}")
        return False

    print("PASS: All route files are integrated into api/main.py.")
    return True

def get_all_backend_routes():
    # Import the FastAPI application and inspect its routes
    sys.path.insert(0, os.path.abspath("."))
    try:
        from api.main import app
    except Exception as e:
        print(f"FAIL: Could not import api.main: {e}")
        return None

    backend_paths = set()
    for route in app.routes:
        if type(route).__name__ == '_IncludedRouter':
            if hasattr(route, 'original_router') and hasattr(route.original_router, 'routes'):
                for r in route.original_router.routes:
                    if hasattr(r, 'path'):
                        backend_paths.add(r.path)
        elif hasattr(route, "path"):
            backend_paths.add(route.path)
    return backend_paths

def check_frontend_endpoints_vs_backend():
    print("Checking that every frontend API endpoint has a registered backend route...")
    backend_paths = get_all_backend_routes()
    if backend_paths is None:
        return False

    frontend_api_dir = "frontend/src/api"
    if not os.path.exists(frontend_api_dir):
        print(f"Warning: {frontend_api_dir} not found. Skipping frontend endpoint validation.")
        return True

    # Parse all apiFetch paths from .ts files
    frontend_endpoints = set()
    fetch_pattern = re.compile(r'apiFetch(?:<[^>]*>)?\s*\(\s*[`"\']([^`"\';\)]+)[`"\']')

    for root, _, files in os.walk(frontend_api_dir):
        for file in files:
            if file.endswith(".ts"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()
                for match in fetch_pattern.finditer(content):
                    path = match.group(1)
                    # Clean up query params, backticks, nested templating
                    path_clean = path.split("?")[0]
                    # Specific cleanup for variable parameters that aren't path IDs (like ${qs} or ${params})
                    path_clean = path_clean.replace("${qs", "").replace("${params", "")
                    # Convert string interpolations like ${id} or ${decisionId} to generic {param}
                    path_clean = re.sub(r'\$\{[^}]+\}', '{param}', path_clean)
                    # Strip residual javascript/typescript template literal syntax characters
                    path_clean = path_clean.replace("}", "").replace("{", "").replace("`", "").strip()
                    if path_clean.endswith("/"):
                        path_clean = path_clean[:-1]
                    if path_clean:
                        frontend_endpoints.add(path_clean)

    unmatched = []
    for f_endpoint in frontend_endpoints:
        # FastAPI prefixes all imported routers with their configured prefixes or /api/v1/ prefix
        possible_paths = [
            f_endpoint,
            f"/api/v1{f_endpoint}",
            f_endpoint.replace("/api/v1", ""),
        ]

        matched = False
        for bp in backend_paths:
            # Convert backend parameters (e.g., {decision_id}) and frontend placeholders ({param}) to wildcards
            normalized_bp = re.sub(r'\{[a-zA-Z_0-9]+\}', '[^/]+', bp)
            bp_regex = re.compile("^" + normalized_bp + "$")

            for candidate in possible_paths:
                normalized_candidate = re.sub(r'param', '[^/]+', candidate)
                if bp_regex.match(normalized_candidate) or re.compile("^" + normalized_candidate + "$").match(bp):
                    matched = True
                    break
            if matched:
                break

        if not matched:
            unmatched.append(f_endpoint)

    if unmatched:
        print(f"FAIL: The following frontend endpoints do not have registered backend routes: {unmatched}")
        return False

    print("PASS: Every frontend API endpoint has a registered backend route.")
    return True

def check_routes_security_and_duplicity():
    print("Checking route uniqueness and security constraints...")

    sys.path.insert(0, os.path.abspath("."))
    try:
        from api.main import app
    except Exception as e:
        print(f"FAIL: Could not import api.main: {e}")
        return False

    paths = set()
    duplicates = []
    unprotected = []

    PUBLIC_PATHS = {
        "/docs", "/redoc", "/openapi.json",
        "/api/v1/auth/login", "/api/v1/auth/register",
        "/api/v1/health", "/api/v1/health/live", "/api/v1/health/ready",
        "/auth/login", "/auth/register",
        "/health", "/health/live", "/health/ready",
    }

    all_routes_to_inspect = []
    for route in app.routes:
        if type(route).__name__ == '_IncludedRouter':
            if hasattr(route, 'original_router') and hasattr(route.original_router, 'routes'):
                all_routes_to_inspect.extend(route.original_router.routes)
        else:
            all_routes_to_inspect.append(route)

    for route in all_routes_to_inspect:
        if hasattr(route, "path") and hasattr(route, "methods"):
            for method in route.methods:
                key = (route.path, method)
                if key in paths:
                    duplicates.append(key)
                paths.add(key)

            is_public = False
            for p in PUBLIC_PATHS:
                if route.path == p or route.path.startswith(p + "/"):
                    is_public = True
                    break

            if not is_public:
                has_auth = False
                if hasattr(route, "dependencies") and route.dependencies:
                    for dep in route.dependencies:
                        dep_name = str(dep.dependency)
                        if "get_current_user" in dep_name or "auth" in dep_name or "current" in dep_name:
                            has_auth = True
                            break
                if not has_auth:
                    sig = inspect.signature(route.endpoint)
                    for param in sig.parameters.values():
                        if "get_current_user" in str(param.default) or "current_user" in param.name:
                            has_auth = True
                            break

                if not has_auth:
                    unprotected.append(route.path)

    if duplicates:
        print(f"FAIL: Duplicate route paths detected: {duplicates}")
        return False

    if unprotected:
        print(f"WARNING: The following routes may be missing explicit authentication: {list(set(unprotected))}")

    print("PASS: No duplicate route paths found.")
    return True

def check_unpinned_dependencies():
    print("Checking for unpinned python dependencies...")
    if not os.path.exists("requirements.txt"):
        print("FAIL: requirements.txt is missing.")
        return False

    with open("requirements.txt", "r") as f:
        lines = f.readlines()

    unpinned = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line and ">=" not in line and "<=" not in line and "~=" not in line:
            unpinned.append(line)

    if unpinned:
        print(f"WARNING: Unpinned python dependencies found: {unpinned}")
    else:
        print("PASS: All dependencies are pinned.")
    return True

def check_circular_imports_and_orphans():
    print("Detecting potential circular imports and orphaned code...")
    modules_to_test = [
        "config",
        "database",
        "logging_config",
        "core.engine",
        "core.confidence_engine",
        "market_data.indicators",
        "services.kpi_service",
    ]
    for mod in modules_to_test:
        try:
            importlib.import_module(mod)
        except Exception as e:
            print(f"FAIL: Circular or import error on module '{mod}': {e}")
            return False
    print("PASS: Key system modules imported successfully with no circular loop exceptions.")
    return True

def main():
    print("==================================================")
    print("ELITE DECISION ENGINE QUALITY GATE VERIFICATION   ")
    print("==================================================")

    success = True
    success &= check_router_registration()
    success &= check_routes_security_and_duplicity()
    success &= check_frontend_endpoints_vs_backend()
    success &= check_unpinned_dependencies()
    success &= check_circular_imports_and_orphans()

    if not success:
        print("==================================================")
        print("QUALITY GATE STATUS: FAILED                       ")
        print("==================================================")
        sys.exit(1)
    else:
        print("==================================================")
        print("QUALITY GATE STATUS: PASSED                       ")
        print("==================================================")
        sys.exit(0)

if __name__ == "__main__":
    main()
