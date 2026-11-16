import json
from playwright.sync_api import sync_playwright

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path, headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    
    # Authenticate via localStorage
    page.goto('http://localhost:3000', wait_until='networkidle')
    page.fill('input[type="email"]', 'demo@flowpilot.ai')
    page.fill('input[type="password"]', 'FlowPilot2026!')
    page.click('button[type="submit"]')
    page.wait_for_timeout(2000)
    
    card_styles = page.evaluate("""() => {
        const card = document.querySelector('.grid a');
        if (!card) return null;
        const cs = window.getComputedStyle(card);
        return {
            bg: cs.backgroundColor,
            backdropFilter: cs.backdropFilter || cs.webkitBackdropFilter,
            borderColor: cs.borderColor,
            boxShadow: cs.boxShadow,
            borderRadius: cs.borderRadius,
            color: cs.color
        };
    }""")
    print('Card computed styles:', json.dumps(card_styles, indent=2))
    
    # Check button styles
    btn_styles = page.evaluate("""() => {
        const btn = document.querySelector('button');
        if (!btn) return null;
        const cs = window.getComputedStyle(btn);
        return {
            bg: cs.backgroundColor,
            borderColor: cs.borderColor,
            borderRadius: cs.borderRadius,
            color: cs.color
        };
    }""")
    print('Button computed styles:', json.dumps(btn_styles, indent=2))
    
    browser.close()
