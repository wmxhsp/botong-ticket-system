---
name: webapp-e2e-testing
description: "End-to-end testing for the Flask+Vue ticket system using Playwright. Invoke when user asks to test the web app, verify UI behavior, run E2E tests, or debug frontend issues with browser automation."
---

# Web Application E2E Testing for Botong Ticket System

End-to-end testing for the Flask + Vue 3 ticket system using Playwright browser automation.

## When to Use

- User asks to test the web application
- User wants to verify a feature works end-to-end
- User needs to debug UI behavior visually
- User requests E2E test automation
- User wants to capture screenshots of the running app

## Architecture

```
Backend:  python app.py          → port 5053
Frontend: npm run dev (Vite)     → port 5173
Database: SQLite (tickets.db)
```

## Setup

```bash
pip install playwright
playwright install chromium
```

## Testing Patterns

### Start Backend + Run Tests

```python
from playwright.sync_api import sync_playwright
import subprocess
import time
import requests

backend = subprocess.Popen(['python', 'app.py'], cwd='/Users/supeng/Documents/botong-ticket-system')
time.sleep(3)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto('http://localhost:5053')
        page.wait_for_load_state('networkidle')

        page.screenshot(path='homepage.png', full_page=True)

        browser.close()
finally:
    backend.terminate()
```

### Login Flow Test

```python
def test_login(page):
    page.goto('http://localhost:5053')
    page.wait_for_load_state('networkidle')

    page.fill('input[type="text"]', 'admin')
    page.fill('input[type="password"]', 'password')
    page.click('button[type="submit"]')

    page.wait_for_url('**/dashboard')
    assert 'dashboard' in page.url.lower()
```

### Ticket CRUD Test

```python
def test_ticket_crud(page):
    page.goto('http://localhost:5053/tickets/create')
    page.wait_for_load_state('networkidle')

    page.fill('#client-select', '测试客户')
    page.fill('#description', 'E2E测试工单')
    page.click('button:has-text("创建")')

    page.wait_for_url('**/tickets/*')
    assert page.locator('text=E2E测试工单').is_visible()
```

### Visual Regression Test

```python
def test_dashboard_visual(page):
    page.goto('http://localhost:5053/dashboard')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)  # Wait for charts to render

    page.screenshot(path='dashboard_baseline.png', full_page=True)
```

### API Integration Test

```python
def test_api_health():
    response = requests.get('http://localhost:5053/api/v1/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_api_tickets_list():
    response = requests.get('http://localhost:5053/api/v1/tickets')
    assert response.status_code == 200
    data = response.json()
    assert 'tickets' in data or isinstance(data, list)
```

## Reconnaissance Pattern

When testing an unfamiliar page:

1. **Navigate and wait**: `page.goto(url)` + `page.wait_for_load_state('networkidle')`
2. **Screenshot**: `page.screenshot(path='inspect.png', full_page=True)`
3. **Inspect DOM**: `page.content()` or `page.locator('button').all()`
4. **Identify selectors**: From rendered state, not source code
5. **Execute actions**: Using discovered selectors

## Common Selectors for This App

| Element | Selector Pattern |
|---------|-----------------|
| Navigation links | `a:has-text("工单")` |
| Bootstrap modals | `.modal.show` |
| Form inputs | `#field-name` or `[name="field"]` |
| Submit buttons | `button[type="submit"]` or `button:has-text("保存")` |
| Toast messages | `.toast-body` or `.alert` |
| Table rows | `table tbody tr` |
| Pagination | `.pagination .page-item` |
| Search/filter | `input[placeholder*="搜索"]` |

## Console Error Capture

```python
console_errors = []
page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)

# ... run tests ...

assert len(console_errors) == 0, f"Console errors: {console_errors}"
```

## Network Request Monitoring

```python
api_requests = []
page.on('request', lambda req: api_requests.append(req.url) if '/api/' in req.url else None)
page.on('response', lambda res: print(f'{res.status} {res.url}') if res.status >= 400 else None)
```

## Best Practices

| Practice | Why |
|----------|-----|
| Always `wait_for_load_state('networkidle')` | Vue apps need time to hydrate |
| Use `headless=True` for CI | No display needed |
| Use `headless=False` for debugging | See what's happening |
| Wait for charts to render (`wait_for_timeout(2000)`) | Chart.js is async |
| Capture console errors | Catch Vue warnings and API errors |
| Test API endpoints directly | Faster than full browser tests |
| Use `full_page=True` for screenshots | Catch layout issues below fold |

## Integration with pytest

```python
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_homepage(page):
    page.goto('http://localhost:5053')
    page.wait_for_load_state('networkidle')
    assert page.title() is not None
```

## Key Reminders

| Rule | Why |
|------|-----|
| Wait for `networkidle` before inspecting | Dynamic content not yet rendered |
| Close browser/context after tests | Prevent resource leaks |
| Don't inspect DOM before waiting | Stale/incomplete elements |
| Use text-based selectors for Bootstrap | More stable than CSS classes |
| Test both API and UI layers | Catch issues at either level |
