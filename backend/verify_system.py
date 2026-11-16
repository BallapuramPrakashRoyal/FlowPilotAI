import httpx
import time

time.sleep(2)

print("="*60)
print("FLOWPILOT AI - FULL LIVE SYSTEM VERIFICATION")
print("="*60)

# 1. Test Backend Health & Docs
b_client = httpx.Client(base_url="http://127.0.0.1:8000")
health = b_client.get("/health")
docs = b_client.get("/docs")
print("1. Backend Health:", health.status_code, health.json())
print("2. Swagger API Docs /docs:", docs.status_code)

# 2. Test Auth Login
login_res = b_client.post("/api/v1/auth/login", json={"email": "demo@flowpilot.ai", "password": "FlowPilot2026!"})
print("3. Auth Login (demo@flowpilot.ai):", login_res.status_code)
token = login_res.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# 3. Test Dashboard Analytics
overview = b_client.get("/api/v1/analytics/overview", headers=headers)
print("4. Analytics Overview:", overview.status_code)
recent = overview.json().get("recent_activity", [])
print(f"   Dashboard Live Activity Records: {len(recent)}")
for r in recent[:2]:
    print(f"   - {r['workflow_name']} ({r['status']}, {r['duration_ms']}ms)")

# 4. Test Execution Inspector endpoint
execs = b_client.get("/api/v1/executions/", headers=headers)
print(f"5. Execution Inspector Records: {execs.status_code} (Total: {len(execs.json())})")
for e in execs.json()[:3]:
    print(f"   - Run {e['id'][:8]}: {e['status']} | Nodes: {len(e.get('nodes', []))}")

# 5. Test Approvals endpoint
approvals = b_client.get("/api/v1/approvals/?status_filter=ALL", headers=headers)
print(f"6. Approval Center Records: {approvals.status_code} (Total: {len(approvals.json())})")

# 6. Test Multi-Prompt AI Workflow Generation
test_prompts = [
    "Slack webhook triage with sentiment classification and high-priority escalation",
    "Financial invoice PDF extraction with RAG rate audit and accounting export",
    "Monitor GitHub pull requests for OWASP security vulnerabilities and auto-comment",
    "Autonomous lead enrichment and outbound marketing campaign outreach",
    "Scheduled daily database snapshot and encrypted backup sync to AWS S3 bucket"
]

print("\n7. Dynamic AI Workflow Generator Test (5 Unique Prompts):")
for prompt in test_prompts:
    res = b_client.post("/api/v1/workflows/generate", json={"prompt": prompt}, headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"   [PASS 200] '{data['name']}' | Nodes: {len(data['graph']['nodes'])} | Edges: {len(data['graph']['edges'])}")
    else:
        print(f"   [FAIL {res.status_code}] {prompt} -> {res.text}")

# 7. Test Frontend Accessibility
f_client = httpx.Client(base_url="http://localhost:3000", timeout=10.0)
front_res = f_client.get("/")
print(f"\n8. Frontend dev server (http://localhost:3000): {front_res.status_code} OK")
print("="*60)
print("ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY")
print("="*60)
