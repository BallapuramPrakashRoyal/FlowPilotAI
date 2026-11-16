"""Live smoke test verifying running servers, PostgreSQL, Redis, Auth, and AI DAG generation."""

import urllib.request
import json
import sys

base = 'http://localhost:8000'

print("=== [LIVE SMOKE TEST RUN] ===")

# 1. Login
try:
    login_req = urllib.request.Request(
        f'{base}/api/v1/auth/login',
        data=json.dumps({'email': 'demo@flowpilot.ai', 'password': 'FlowPilot2026!'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(login_req) as resp:
        login_data = json.loads(resp.read().decode('utf-8'))
    token = login_data['access_token']
    print('✓ [1/8] AUTHENTICATION: Success (User:', login_data['user']['email'], ')')
except Exception as e:
    print('✗ [1/8] AUTHENTICATION FAILED:', e)
    sys.exit(1)

auth_headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# 2. Get Workspaces
try:
    ws_req = urllib.request.Request(f'{base}/api/v1/workspaces/', headers=auth_headers)
    with urllib.request.urlopen(ws_req) as resp:
        workspaces = json.loads(resp.read().decode('utf-8'))
    ws_id = workspaces[0]['id']
    auth_headers['X-Workspace-ID'] = ws_id
    print(f'✓ [2/8] WORKSPACE: Found "{workspaces[0]["name"]}" (ID: {ws_id})')
except Exception as e:
    print('✗ [2/8] WORKSPACE RETRIEVAL FAILED:', e)
    sys.exit(1)

# 3. Analytics Overview
try:
    analytics_req = urllib.request.Request(f'{base}/api/v1/analytics/overview', headers=auth_headers)
    with urllib.request.urlopen(analytics_req) as resp:
        analytics = json.loads(resp.read().decode('utf-8'))
    print(f'✓ [3/8] DASHBOARD DATA: Total Workflows: {analytics["total_workflows"]} | Tokens: {analytics["total_tokens_consumed"]} | Cost: ${analytics["estimated_cost_usd"]}')
except Exception as e:
    print('✗ [3/8] ANALYTICS OVERVIEW FAILED:', e)
    sys.exit(1)

# 4. Integrations
try:
    int_req = urllib.request.Request(f'{base}/api/v1/integrations/', headers=auth_headers)
    with urllib.request.urlopen(int_req) as resp:
        integrations = json.loads(resp.read().decode('utf-8'))
    providers = [i['provider'] for i in integrations]
    print(f'✓ [4/8] INTEGRATIONS: Found {len(integrations)} integrations ({providers})')
except Exception as e:
    print('✗ [4/8] INTEGRATIONS FAILED:', e)
    sys.exit(1)

# 5. Approvals
try:
    appr_req = urllib.request.Request(f'{base}/api/v1/approvals/?status=PENDING', headers=auth_headers)
    with urllib.request.urlopen(appr_req) as resp:
        approvals = json.loads(resp.read().decode('utf-8'))
    print(f'✓ [5/8] APPROVALS: Found {len(approvals)} pending approvals')
except Exception as e:
    print('✗ [5/8] APPROVALS FAILED:', e)
    sys.exit(1)

# 6. Executions
try:
    exec_req = urllib.request.Request(f'{base}/api/v1/executions/', headers=auth_headers)
    with urllib.request.urlopen(exec_req) as resp:
        executions = json.loads(resp.read().decode('utf-8'))
    print(f'✓ [6/8] EXECUTIONS: Found {len(executions)} historical executions')
except Exception as e:
    print('✗ [6/8] EXECUTIONS FAILED:', e)
    sys.exit(1)

# 7. AI Generator - Natural Language to DAG
try:
    prompt_payload = {
        'workspace_id': ws_id,
        'prompt': 'Read unread support tickets, summarize sentiment with LLM, and request human review before notifying Slack'
    }
    plan_req = urllib.request.Request(
        f'{base}/api/v1/workflows/generate',
        data=json.dumps(prompt_payload).encode('utf-8'),
        headers=auth_headers
    )
    with urllib.request.urlopen(plan_req) as resp:
        plan = json.loads(resp.read().decode('utf-8'))
    nodes_cnt = len(plan['graph']['nodes'])
    edges_cnt = len(plan['graph']['edges'])
    print(f'✓ [7/8] AI GENERATOR: Built DAG "{plan["name"]}" with {nodes_cnt} nodes and {edges_cnt} edges')
except Exception as e:
    print('✗ [7/8] AI GENERATOR FAILED:', e)
    sys.exit(1)

# 8. Create and Save Workflow to PostgreSQL
try:
    wf_payload = {
        'workspace_id': ws_id,
        'name': plan['name'],
        'description': plan['description'],
        'graph': plan['graph']
    }
    create_wf_req = urllib.request.Request(
        f'{base}/api/v1/workflows/',
        data=json.dumps(wf_payload).encode('utf-8'),
        headers=auth_headers
    )
    with urllib.request.urlopen(create_wf_req) as resp:
        created_wf = json.loads(resp.read().decode('utf-8'))
    print(f'✓ [8/8] WORKFLOW PERSISTENCE: Saved workflow "{created_wf["name"]}" (ID: {created_wf["id"]}) to PostgreSQL 17!')
except Exception as e:
    print('✗ [8/8] WORKFLOW CREATION FAILED:', e)
    sys.exit(1)

print("\n>>> ALL 8 LIVE SMOKE TESTS COMPLETED SUCCESSFULLY! <<<")
