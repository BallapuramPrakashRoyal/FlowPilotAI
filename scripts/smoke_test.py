"""FlowPilot AI — Production Smoke Test & Health Check Suite.

Validates end-to-end infrastructure, API readiness, authenticated access,
and frontend availability without side effects.
"""

import sys
import json
import urllib.request
import urllib.error

BACKEND_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:3000"

DEMO_EMAIL = "demo@flowpilot.ai"
DEMO_PASS = "FlowPilot2026!"


def log_test(name: str, passed: bool, detail: str = ""):
    mark = "[\033[92mPASS\033[0m]" if passed else "[\033[91mFAIL\033[0m]"
    print(f"{mark} {name:<45} {detail}")
    return passed


def run_smoke_tests():
    print(f"=== FlowPilot AI Production Smoke Tests ===")
    print(f"Backend: {BACKEND_BASE} | Frontend: {FRONTEND_BASE}\n")
    
    all_passed = True

    # 1. Backend Liveness (/health)
    try:
        with urllib.request.urlopen(f"{BACKEND_BASE}/health", timeout=5) as resp:
            data = json.loads(resp.read().decode())
            ok = resp.status == 200 and data.get("status") == "healthy"
            all_passed &= log_test("Backend Liveness (/health)", ok, f"v{data.get('version')}")
    except Exception as e:
        all_passed &= log_test("Backend Liveness (/health)", False, str(e))

    # 2. Backend Readiness (/ready)
    try:
        with urllib.request.urlopen(f"{BACKEND_BASE}/ready", timeout=5) as resp:
            data = json.loads(resp.read().decode())
            db_engine = data.get("database", {}).get("engine", "unknown")
            all_passed &= log_test("Backend Readiness (/ready)", resp.status in [200, 503], f"DB: {db_engine}")
    except Exception as e:
        all_passed &= log_test("Backend Readiness (/ready)", False, str(e))

    # 3. Authenticated Login Flow
    token = None
    try:
        req = urllib.request.Request(
            f"{BACKEND_BASE}/api/v1/auth/login",
            data=json.dumps({"email": DEMO_EMAIL, "password": DEMO_PASS}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            token = data.get("access_token")
            all_passed &= log_test("Auth Login Verification", bool(token), f"User: {data.get('user', {}).get('email')}")
    except Exception as e:
        all_passed &= log_test("Auth Login Verification", False, str(e))

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 4. Workspace Access
    workspace_id = None
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/workspaces", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            workspace_id = data[0]["id"] if data else None
            all_passed &= log_test("Workspace Authorization", len(data) > 0, f"Found {len(data)} workspace(s)")
    except Exception as e:
        all_passed &= log_test("Workspace Authorization", False, str(e))

    if workspace_id:
        headers["X-Workspace-ID"] = workspace_id

    # 5. Production Workflow Templates
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/workflows/templates", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            all_passed &= log_test("Production Templates Registry", len(data) >= 7, f"{len(data)} templates loaded")
    except Exception as e:
        all_passed &= log_test("Production Templates Registry", False, str(e))

    # 6. Analytics Overview
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/analytics/overview", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            all_passed &= log_test("Analytics Telemetry Service", "total_workflows" in data, f"Workflows: {data.get('total_workflows')}")
    except Exception as e:
        all_passed &= log_test("Analytics Telemetry Service", False, str(e))

    # 7. Integrations Configuration
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/integrations/config", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            all_passed &= log_test("Integrations Hub Config", "scopes" in data, f"{len(data.get('scopes', []))} OAuth scopes")
    except Exception as e:
        all_passed &= log_test("Integrations Hub Config", False, str(e))

    # 8. Frontend Root & Static Assets
    for route in ["/", "/studio", "/workflows", "/executions", "/integrations"]:
        try:
            with urllib.request.urlopen(f"{FRONTEND_BASE}{route}", timeout=5) as resp:
                all_passed &= log_test(f"Frontend Route ({route})", resp.status == 200, f"HTTP {resp.status}")
        except Exception as e:
            all_passed &= log_test(f"Frontend Route ({route})", False, str(e))

    print("\n" + ("=" * 60))
    if all_passed:
        print("\033[92m[+] All smoke test checks PASSED cleanly.\033[0m")
        return 0
    else:
        print("\033[91m[-] Some smoke test checks FAILED. Inspect details above.\033[0m")
        return 1


if __name__ == "__main__":
    sys.exit(run_smoke_tests())
