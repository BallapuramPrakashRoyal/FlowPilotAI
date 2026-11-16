from playwright.sync_api import sync_playwright

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path, headless=True)
    page = browser.new_page(viewport={'width': 375, 'height': 812})
    page.goto('http://localhost:3000', wait_until='networkidle')
    page.fill('input[type="email"]', 'demo@flowpilot.ai')
    page.fill('input[type="password"]', 'FlowPilot2026!')
    page.click('button[type="submit"]')
    page.wait_for_timeout(2000)
    
    sidebar_w = page.evaluate('document.querySelector("aside") ? document.querySelector("aside").getBoundingClientRect().width : 0')
    main_w = page.evaluate('document.querySelector("main") ? document.querySelector("main").getBoundingClientRect().width : 0')
    print('Mobile 375px: Sidebar width =', sidebar_w, ', Main width =', main_w)
    browser.close()
