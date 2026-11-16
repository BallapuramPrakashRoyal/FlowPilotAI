import urllib.request
import json

base = 'http://localhost:8000'

# Login
payload = json.dumps({'email': 'demo@flowpilot.ai', 'password': 'FlowPilot2026!'}).encode()
req = urllib.request.Request(f'{base}/api/v1/auth/login', data=payload, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    tok = json.loads(r.read())['access_token']

# Workspace
req2 = urllib.request.Request(f'{base}/api/v1/workspaces/', headers={'Authorization': f'Bearer {tok}'})
with urllib.request.urlopen(req2) as r:
    ws_id = json.loads(r.read())[0]['id']

# Executions
req3 = urllib.request.Request(f'{base}/api/v1/executions/', headers={'Authorization': f'Bearer {tok}', 'X-Workspace-ID': ws_id})
with urllib.request.urlopen(req3) as r:
    execs = json.loads(r.read())

print(f"VERIFIED EXECUTIONS IN DATABASE: {len(execs)}")
for e in execs:
    print(f" - ID: {e['id']} | Status: {e['status']} | Nodes: {len(e['nodes'])} | Trigger: {e['trigger_type']}")

# Approvals
req4 = urllib.request.Request(f'{base}/api/v1/approvals/?status=PENDING', headers={'Authorization': f'Bearer {tok}', 'X-Workspace-ID': ws_id})
with urllib.request.urlopen(req4) as r:
    apprs = json.loads(r.read())

print(f"\nVERIFIED PENDING APPROVALS IN DATABASE: {len(apprs)}")
for a in apprs:
    print(f" - Approval ID: {a['id']} | Title: {a['title']} | Action: {a['action_type']}")

# Analytics Overview
req5 = urllib.request.Request(f'{base}/api/v1/analytics/overview', headers={'Authorization': f'Bearer {tok}', 'X-Workspace-ID': ws_id})
with urllib.request.urlopen(req5) as r:
    analytics = json.loads(r.read())

print(f"\nVERIFIED DASHBOARD ANALYTICS:")
print(f" - Total Workflows: {analytics['total_workflows']}")
print(f" - Pending Approvals: {analytics['pending_approvals']}")
print(f" - Successful Executions: {analytics['successful_executions']}")
print(f" - Recent Activity Count: {len(analytics['recent_activity'])}")
for ra in analytics['recent_activity']:
    print(f"   * Activity: {ra['workflow_name']} -> Status: {ra['status']} ({ra['duration_ms']}ms)")
