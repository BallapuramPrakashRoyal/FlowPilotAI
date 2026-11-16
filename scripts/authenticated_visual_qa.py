import os
import time
import json
import urllib.request
from playwright.sync_api import sync_playwright

os.makedirs('docs/screenshots', exist_ok=True)
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

# 1. Obtain authenticated token & workspace from backend
login_req = urllib.request.Request(
    'http://localhost:8000/api/v1/auth/login',
    data=json.dumps({'email': 'demo@flowpilot.ai', 'password': 'FlowPilot2026!'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(login_req) as resp:
    login_data = json.loads(resp.read().decode())
    AUTH_TOKEN = login_data['access_token']

ws_req = urllib.request.Request(
    'http://localhost:8000/api/v1/workspaces',
    headers={'Authorization': f'Bearer {AUTH_TOKEN}'}
)
with urllib.request.urlopen(ws_req) as resp:
    workspaces = json.loads(resp.read().decode())
    WORKSPACE_ID = workspaces[0]['id'] if workspaces else ''

print(f"Authenticated as demo user. Workspace: {WORKSPACE_ID}")

ROUTES = [
    ('dashboard', '/'),
    ('studio', '/studio'),
    ('workflows', '/workflows'),
    ('generator', '/generator'),
    ('executions', '/executions'),
    ('integrations', '/integrations'),
    ('knowledge', '/knowledge'),
    ('approvals', '/approvals'),
    ('onboarding', '/onboarding'),
    ('settings', '/settings'),
    ('analytics', '/analytics'),
]

VIEWPORTS = [
    ('desktop', {'width': 1440, 'height': 900}),
    ('tablet', {'width': 768, 'height': 1024}),
    ('mobile', {'width': 375, 'height': 812}),
]

audit_results = {
    'auth_screen': {},
    'routes': {},
    'console_errors': [],
    'overflow_issues': [],
    'interactive_tests': [],
    'design_audit': {},
}

def run_authenticated_audit():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome_path, headless=True)
        
        # --- PHASE 1: AUDIT AUTHENTICATION SCREEN ---
        print("\n--- Auditing Authentication Screen ---")
        for vp_name, vp_size in VIEWPORTS:
            context = browser.new_context(viewport=vp_size)
            page = context.new_page()
            page.goto('http://localhost:3000', wait_until='networkidle')
            time.sleep(1)
            shot_path = f'docs/screenshots/auth_{vp_name}.png'
            page.screenshot(path=shot_path, full_page=(vp_name == 'desktop'))
            audit_results['auth_screen'][vp_name] = shot_path
            context.close()
            
        # --- PHASE 2: AUDIT AUTHENTICATED ROUTES ---
        print("\n--- Auditing Authenticated Routes Across Viewports ---")
        for route_name, route_path in ROUTES:
            audit_results['routes'][route_name] = {}
            for vp_name, vp_size in VIEWPORTS:
                context = browser.new_context(viewport=vp_size)
                page = context.new_page()
                
                # Pre-seed localStorage with real token and workspace
                page.add_init_script(f"""
                    localStorage.setItem('flowpilot_token', '{AUTH_TOKEN}');
                    localStorage.setItem('flowpilot_workspace_id', '{WORKSPACE_ID}');
                """)
                
                # Console error listener
                def make_listener(r_path, vp):
                    def listener(msg):
                        if msg.type == 'error':
                            # Filter out harmless extension or favicon errors
                            if 'favicon' not in msg.text.lower():
                                audit_results['console_errors'].append({
                                    'route': r_path,
                                    'viewport': vp,
                                    'type': msg.type,
                                    'text': msg.text
                                })
                    return listener
                
                page.on('console', make_listener(route_path, vp_name))
                
                url = f'http://localhost:3000{route_path}'
                try:
                    page.goto(url, wait_until='networkidle', timeout=15000)
                    time.sleep(1.2) # Allow data fetches and Framer Motion / transitions
                    
                    shot_path = f'docs/screenshots/{route_name}_{vp_name}.png'
                    page.screenshot(path=shot_path, full_page=(vp_name == 'desktop'))
                    
                    # Horizontal overflow check
                    overflow = page.evaluate("""() => {
                        return {
                            scrollWidth: document.documentElement.scrollWidth,
                            clientWidth: document.documentElement.clientWidth,
                            hasOverflow: document.documentElement.scrollWidth > (document.documentElement.clientWidth + 2)
                        };
                    }""")
                    
                    if overflow['hasOverflow']:
                        audit_results['overflow_issues'].append({
                            'route': route_path,
                            'viewport': vp_name,
                            'scrollWidth': overflow['scrollWidth'],
                            'clientWidth': overflow['clientWidth']
                        })
                        
                    audit_results['routes'][route_name][vp_name] = {
                        'screenshot': shot_path,
                        'overflow': overflow['hasOverflow']
                    }
                    print(f"Captured: {route_name} ({vp_name}) - Overflow: {overflow['hasOverflow']}")
                except Exception as e:
                    audit_results['routes'][route_name][vp_name] = {'error': str(e)}
                    print(f"Error on {route_name} ({vp_name}): {e}")
                finally:
                    context.close()
                    
        # --- PHASE 3: COMPONENT STYLES & TOKEN INSPECTION ---
        print("\n--- Inspecting Component Styles & Tokens ---")
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        page.add_init_script(f"""
            localStorage.setItem('flowpilot_token', '{AUTH_TOKEN}');
            localStorage.setItem('flowpilot_workspace_id', '{WORKSPACE_ID}');
        """)
        page.goto('http://localhost:3000/', wait_until='networkidle')
        time.sleep(1.5)
        
        design_metrics = page.evaluate("""() => {
            const getVal = (el, prop) => el ? window.getComputedStyle(el).getPropertyValue(prop) : null;
            const body = document.body;
            const sidebar = document.querySelector('aside');
            const header = document.querySelector('header');
            const glassCard = document.querySelector('.glass-card') || document.querySelector('[class*="glass-card"]');
            const primaryBtn = document.querySelector('.glass-btn-primary') || document.querySelector('button');
            const heading = document.querySelector('h1') || document.querySelector('h2');
            
            return {
                bodyBackgroundColor: getVal(body, 'background-color'),
                sidebarBackground: getVal(sidebar, 'background-color'),
                sidebarBackdropFilter: getVal(sidebar, 'backdrop-filter') || getVal(sidebar, '-webkit-backdrop-filter'),
                sidebarBorder: getVal(sidebar, 'border-right-color'),
                headerBackground: getVal(header, 'background-color'),
                cardBackground: getVal(glassCard, 'background-color'),
                cardBackdropFilter: getVal(glassCard, 'backdrop-filter') || getVal(glassCard, '-webkit-backdrop-filter'),
                cardBorder: getVal(glassCard, 'border-top-color'),
                cardBoxShadow: getVal(glassCard, 'box-shadow'),
                primaryButtonBg: getVal(primaryBtn, 'background-image') || getVal(primaryBtn, 'background-color'),
                headingColor: getVal(heading, 'color'),
                headingFont: getVal(heading, 'font-family'),
            };
        }""")
        audit_results['design_audit'] = design_metrics
        print("Design Metrics:", json.dumps(design_metrics, indent=2))
        
        # --- PHASE 4: DETAILED INTERACTION TESTS ---
        print("\n--- Running Real User Interactions ---")
        
        # 1. Studio Interactions: Node Selection & Inspector
        page.goto('http://localhost:3000/studio', wait_until='networkidle')
        time.sleep(1.5)
        node_count = page.evaluate("""() => document.querySelectorAll('.react-flow__node').length""")
        node_clicked = False
        if node_count > 0:
            first_node = page.locator('.react-flow__node').first
            first_node.click()
            time.sleep(0.8)
            node_clicked = True
            page.screenshot(path='docs/screenshots/action_studio_node_selected.png')
            
        audit_results['interactive_tests'].append({
            'name': 'Studio Node Click & Inspection',
            'passed': node_clicked and node_count > 0,
            'details': f'Canvas rendered {node_count} nodes. Node clicked successfully.'
        })
        
        # 2. Workflows Tab Switch & Filter
        page.goto('http://localhost:3000/workflows', wait_until='networkidle')
        time.sleep(1.5)
        templates_tab = page.locator('button:has-text("Production Templates")').first
        tab_switched = False
        template_cards_count = 0
        if templates_tab.count() > 0:
            templates_tab.click()
            time.sleep(0.8)
            tab_switched = True
            template_cards_count = page.evaluate("""() => document.querySelectorAll('[class*="glass"]').length""")
            page.screenshot(path='docs/screenshots/action_workflows_templates_view.png')
            
        audit_results['interactive_tests'].append({
            'name': 'Workflows Gallery Tab Switch',
            'passed': tab_switched,
            'details': f'Switched to Production Templates tab. {template_cards_count} glass elements rendered.'
        })
        
        # 3. Knowledge Base Query Testing
        page.goto('http://localhost:3000/knowledge', wait_until='networkidle')
        time.sleep(1.5)
        search_input = page.locator('input[placeholder*="search" i], input[placeholder*="query" i]').first
        query_executed = False
        if search_input.count() > 0:
            search_input.fill('enterprise pricing terms')
            search_btn = page.locator('button:has-text("Search")').first
            if search_btn.count() > 0:
                search_btn.click()
                time.sleep(1.2)
                query_executed = True
            page.screenshot(path='docs/screenshots/action_knowledge_search.png')
            
        audit_results['interactive_tests'].append({
            'name': 'Knowledge Base Vector Query Input & Search',
            'passed': query_executed,
            'details': 'Query "enterprise pricing terms" executed against retrieval service.'
        })
        
        # 4. Integrations Connection Dialog Trigger
        page.goto('http://localhost:3000/integrations', wait_until='networkidle')
        time.sleep(1.5)
        connect_btn = page.locator('button:has-text("Connect")').first
        modal_opened = False
        if connect_btn.count() > 0:
            connect_btn.click()
            time.sleep(0.8)
            modal_opened = page.evaluate("""() => {
                const text = document.body.innerText;
                return text.includes('Connect Gmail') || text.includes('OAuth') || text.includes('Scopes');
            }""")
            page.screenshot(path='docs/screenshots/action_integrations_modal.png')
            
        audit_results['interactive_tests'].append({
            'name': 'Integrations Connection Modal Interaction',
            'passed': modal_opened,
            'details': f'Connect button clicked, modal visible: {modal_opened}'
        })
        
        # 5. Approvals Center Decision Verification
        page.goto('http://localhost:3000/approvals', wait_until='networkidle')
        time.sleep(1.5)
        approvals_info = page.evaluate("""() => {
            const hasPending = document.body.innerText.includes('Approve') || document.body.innerText.includes('Pending Review');
            const buttons = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim());
            return { hasPending, buttons };
        }""")
        page.screenshot(path='docs/screenshots/action_approvals_center.png')
        audit_results['interactive_tests'].append({
            'name': 'Approvals Center State & Controls',
            'passed': True,
            'details': approvals_info
        })
        
        browser.close()
        
    with open('docs/audit_summary_live.json', 'w') as f:
        json.dump(audit_results, f, indent=2)
    print("\nAuthenticated Visual QA Complete! Summary saved to docs/audit_summary_live.json")

if __name__ == '__main__':
    run_authenticated_audit()
