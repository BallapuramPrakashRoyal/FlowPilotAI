"""FlowPilot AI — Comprehensive Security & Production Audit Script.

Scans the codebase for:
1. Debug endpoints and backdoor routes.
2. Insecure CORS wildcards.
3. Hardcoded secrets outside config defaults.
4. Exposed sensitive keys in frontend assets.
5. Container and docker configurations.
"""

import os
import re
import json

AUDIT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

results = {
    "debug_endpoints": [],
    "insecure_cors": [],
    "hardcoded_secrets": [],
    "frontend_secret_leaks": [],
    "docker_checks": [],
}

# 1. Search for debug endpoints in API routes
debug_regex = re.compile(r'@router\.(get|post|put|delete)\([\'\"].*debug.*[\'\"]\)', re.I)
for root, _, files in os.walk(os.path.join(AUDIT_DIR, "backend", "app", "api")):
    for f in files:
        if f.endswith(".py"):
            fpath = os.path.join(root, f)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for idx, line in enumerate(fp, 1):
                    if debug_regex.search(line):
                        results["debug_endpoints"].append({
                            "file": os.path.relpath(fpath, AUDIT_DIR),
                            "line": idx,
                            "content": line.strip()
                        })

# 2. Check CORS configuration
config_path = os.path.join(AUDIT_DIR, "backend", "app", "core", "config.py")
with open(config_path, "r", encoding="utf-8") as fp:
    content = fp.read()
    if 'allow_origins=["*"]' in content or 'ALLOWED_ORIGINS: List[str] = ["*"]' in content:
        results["insecure_cors"].append("Wildcard CORS detected in config.py")

# 3. Check for hardcoded API keys or credentials
sensitive_regex = re.compile(r'(AIzaSy[A-Za-z0-9_-]{33}|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{36})')
for root, _, files in os.walk(AUDIT_DIR):
    # Skip git, venv, node_modules, tests
    if any(ignore in root for ignore in [".git", ".venv", "node_modules", ".next", "backups", "tests"]):
        continue
    for f in files:
        if f.endswith((".py", ".ts", ".tsx", ".js", ".json", ".yml", ".yaml")):
            fpath = os.path.join(root, f)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for idx, line in enumerate(fp, 1):
                    m = sensitive_regex.search(line)
                    if m:
                        results["hardcoded_secrets"].append({
                            "file": os.path.relpath(fpath, AUDIT_DIR),
                            "line": idx,
                            "match": m.group(0)[:8] + "..."
                        })

# 4. Check Frontend for accidental backend secret imports
for root, _, files in os.walk(os.path.join(AUDIT_DIR, "frontend", "src")):
    for f in files:
        if f.endswith((".ts", ".tsx", ".js")):
            fpath = os.path.join(root, f)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for idx, line in enumerate(fp, 1):
                    if any(secret in line for secret in ["SECRET_KEY", "CREDENTIAL_ENCRYPTION_KEY", "POSTGRES_PASSWORD", "GOOGLE_CLIENT_SECRET"]):
                        # Allow harmless string labels or UI documentation
                        if "process.env" in line:
                            results["frontend_secret_leaks"].append({
                                "file": os.path.relpath(fpath, AUDIT_DIR),
                                "line": idx,
                                "content": line.strip()
                            })

# 5. Check Dockerfile non-root directives
backend_docker = os.path.join(AUDIT_DIR, "backend", "Dockerfile")
with open(backend_docker, "r") as fp:
    c = fp.read()
    results["docker_checks"].append({
        "container": "backend",
        "has_non_root_user": "USER appuser" in c,
        "has_healthcheck": "HEALTHCHECK" in c,
        "has_stopsignal": "STOPSIGNAL SIGTERM" in c
    })

frontend_docker = os.path.join(AUDIT_DIR, "frontend", "Dockerfile")
with open(frontend_docker, "r") as fp:
    c = fp.read()
    results["docker_checks"].append({
        "container": "frontend",
        "has_non_root_user": "USER nextjs" in c,
        "has_healthcheck": "HEALTHCHECK" in c,
        "has_stopsignal": "STOPSIGNAL SIGTERM" in c
    })

with open(os.path.join(AUDIT_DIR, "docs", "security_audit_results.json"), "w") as fp:
    json.dump(results, fp, indent=2)

print("Security Audit Results:")
print(f"Debug endpoints found: {len(results['debug_endpoints'])}")
print(f"Insecure CORS issues: {len(results['insecure_cors'])}")
print(f"Hardcoded API keys: {len(results['hardcoded_secrets'])}")
print(f"Frontend secret leaks: {len(results['frontend_secret_leaks'])}")
for dc in results["docker_checks"]:
    print(f"Docker [{dc['container']}]: Non-root: {dc['has_non_root_user']}, Healthcheck: {dc['has_healthcheck']}, StopSignal: {dc['has_stopsignal']}")
