import urllib.request
import json
import time

base = 'http://localhost:8000'
payload = json.dumps({'email': 'demo@flowpilot.ai', 'password': 'FlowPilot2026!'}).encode()
req = urllib.request.Request(f'{base}/api/v1/auth/login', data=payload, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    tok = json.loads(r.read())['access_token']

req2 = urllib.request.Request(f'{base}/api/v1/workspaces/', headers={'Authorization': f'Bearer {tok}'})
with urllib.request.urlopen(req2) as r:
    ws_id = json.loads(r.read())[0]['id']

# Get active workflow
req3 = urllib.request.Request(f'{base}/api/v1/workflows/', headers={'Authorization': f'Bearer {tok}', 'X-Workspace-ID': ws_id})
with urllib.request.urlopen(req3) as r:
    wfs = json.loads(r.read())

wf = wfs[0]
wf_id = wf['id']
print(f"Triggering execution for workflow: {wf['name']} (ID: {wf_id})")

req4 = urllib.request.Request(
    f'{base}/api/v1/workflows/{wf_id}/execute',
    data=b'{}',
    headers={'Authorization': f'Bearer {tok}', 'X-Workspace-ID': ws_id, 'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req4) as r:
    exc = json.loads(r.read())

print(f"Execution created: ID {exc['id']} | Status: {exc['status']}")

# Wait 2 seconds for runner background task to advance nodes
time.sleep(2)

# Check execution status
req5 = urllib.request.Request(f'{base}/api/v1/executions/{exc["id"]}', headers={'Authorization': f'Bearer {tok}', 'X-Workspace-ID': ws_id})
with urllib.request.urlopen(req5) as r:
    exc_after = json.loads(r.read())

print(f"Execution state: ID {exc_after['id']} | Status: {exc_after['status']} | Nodes count: {len(exc_after['nodes'])}")
for n in exc_after['nodes']:
    print(f"  - Node {n['node_id']} ({n['node_type']}) -> Status: {n['status']}")

# Check pending approvals
req6 = urllib.request.Request(f'{base}/api/v1/approvals/?status_filter=PENDING', headers={'Authorization': f'Bearer {tok}', 'X-Workspace-ID': ws_id})
with urllib.request.urlopen(req6) as r:
    apprs = json.loads(r.read())

print(f"\nPending approvals currently in system: {len(apprs)}")
for a in apprs:
    print(f"  - Approval ID: {a['id'][:8]} | Title: {a['title']}")
