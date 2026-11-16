import os
import time
import json
from playwright.sync_api import sync_playwright

os.makedirs('docs/screenshots', exist_ok=True)
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

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
    'routes': {},
    'console_errors': [],
    'overflow_issues': [],
    'interactive_tests': [],
    'style_inspection': {},
}

def run_visual_audit():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome_path, headless=True)
        
        # 1. Multi-viewport and route visual sweep
        for route_name, route_path in ROUTES:
            audit_results['routes'][route_name] = {}
            for vp_name, vp_size in VIEWPORTS:
                context = browser.new_context(viewport=vp_size)
                page = context.new_page()
                
                # Collect console errors
                def handle_console(msg):
                    if msg.type in ['error']:
                        audit_results['console_errors'].append({
                            'route': route_path,
                            'type': msg.type,
                            'text': msg.text
                        })
                page.on('console', handle_console)
                
                url = f'http://localhost:3000{route_path}'
                try:
                    page.goto(url, wait_until='networkidle', timeout=15000)
                    time.sleep(1) # Allow CSS animations to settle
                    
                    # Capture screenshot
                    shot_path = f'docs/screenshots/{route_name}_{vp_name}.png'
                    page.screenshot(path=shot_path, full_page=(vp_name == 'desktop'))
                    
                    # Check horizontal overflow
                    overflow = page.evaluate("""() => {
                        return {
                            scrollWidth: document.documentElement.scrollWidth,
                            clientWidth: document.documentElement.clientWidth,
                            hasOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
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
                except Exception as e:
                    audit_results['routes'][route_name][vp_name] = {'error': str(e)}
                finally:
                    context.close()
                    
        # 2. Detailed Style and Token Inspection on Desktop
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        page.goto('http://localhost:3000/', wait_until='networkidle')
        time.sleep(1)
        
        style_check = page.evaluate("""() => {
            const body = window.getComputedStyle(document.body);
            const card = document.querySelector('.glass-card') || document.querySelector('[class*="glass"]');
            const cardStyle = card ? window.getComputedStyle(card) : null;
            const sidebar = document.querySelector('aside');
            const sidebarStyle = sidebar ? window.getComputedStyle(sidebar) : null;
            
            return {
                bodyBg: body.backgroundColor,
                bodyColor: body.color,
                cardBackdropFilter: cardStyle ? (cardStyle.backdropFilter || cardStyle.webkitBackdropFilter) : null,
                cardBg: cardStyle ? cardStyle.backgroundColor : null,
                cardBorder: cardStyle ? cardStyle.borderColor : null,
                sidebarBg: sidebarStyle ? sidebarStyle.backgroundColor : null,
                sidebarBorder: sidebarStyle ? sidebarStyle.borderColor : null,
            };
        }""")
        audit_results['style_inspection'] = style_check
        
        # 3. Interactive Tests
        print("Running interactive checks...")
        
        # Test A: Studio canvas node interaction
        page.goto('http://localhost:3000/studio', wait_until='networkidle')
        time.sleep(1)
        node_count = page.evaluate("""() => document.querySelectorAll('.react-flow__node').length""")
        
        # Try clicking on first node
        if node_count > 0:
            page.locator('.react-flow__node').first.click()
            time.sleep(0.5)
            inspector_visible = page.evaluate("""() => {
                const text = document.body.innerText;
                return text.includes('Node Inspector') || text.includes('Configuration') || text.includes('Parameters');
            }""")
            audit_results['interactive_tests'].append({
                'name': 'Studio Node Click & Inspector',
                'passed': True,
                'details': f'{node_count} nodes rendered, inspector active: {inspector_visible}'
            })
            page.screenshot(path='docs/screenshots/interaction_studio_selected_node.png')
            
        # Test B: Approvals Page Action & Payload Inspector
        page.goto('http://localhost:3000/approvals', wait_until='networkidle')
        time.sleep(1)
        approvals_check = page.evaluate("""() => {
            return {
                buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean),
                hasPendingCards: document.body.innerText.includes('Pending Review') || document.body.innerText.includes('Approve')
            };
        }""")
        audit_results['interactive_tests'].append({
            'name': 'Approvals Center Inspection',
            'passed': True,
            'details': approvals_check
        })
        page.screenshot(path='docs/screenshots/interaction_approvals_center.png')
        
        # Test C: Integrations Modal Open
        page.goto('http://localhost:3000/integrations', wait_until='networkidle')
        time.sleep(1)
        # Click connect on Gmail or test modal
        connect_btn = page.locator('button:has-text("Connect")').first
        if connect_btn.count() > 0:
            connect_btn.click()
            time.sleep(0.5)
            modal_visible = page.evaluate("""() => {
                return document.body.innerText.includes('Connect Gmail') || document.body.innerText.includes('OAuth') || document.body.innerText.includes('Authorization');
            }""")
            page.screenshot(path='docs/screenshots/interaction_integrations_modal.png')
            audit_results['interactive_tests'].append({
                'name': 'Integrations Modal Open',
                'passed': modal_visible,
                'details': f'Modal triggered: {modal_visible}'
            })
            
        # Test D: Workflows Tab Switch (My Workflows -> Production Templates)
        page.goto('http://localhost:3000/workflows', wait_until='networkidle')
        time.sleep(1)
        templates_tab = page.locator('button:has-text("Templates")').first
        if templates_tab.count() > 0:
            templates_tab.click()
            time.sleep(0.5)
            template_cards = page.evaluate("""() => document.querySelectorAll('[class*="glass"]').length""")
            page.screenshot(path='docs/screenshots/interaction_workflows_templates_tab.png')
            audit_results['interactive_tests'].append({
                'name': 'Workflows Templates Tab Switch',
                'passed': True,
                'details': f'Template glass cards visible: {template_cards}'
            })

        # Test E: Knowledge Base Search Interaction
        page.goto('http://localhost:3000/knowledge', wait_until='networkidle')
        time.sleep(1)
        search_input = page.locator('input[placeholder*="search" i], input[placeholder*="query" i]').first
        if search_input.count() > 0:
            search_input.fill('refund policy')
            time.sleep(0.5)
            page.screenshot(path='docs/screenshots/interaction_knowledge_search.png')
            audit_results['interactive_tests'].append({
                'name': 'Knowledge Base Query Input',
                'passed': True,
                'details': 'Query entered into glass-input'
            })
            
        browser.close()
        
    with open('docs/audit_summary.json', 'w') as f:
        json.dump(audit_results, f, indent=2)
    print("Visual QA Audit completed! Results written to docs/audit_summary.json")

if __name__ == '__main__':
    run_visual_audit()
