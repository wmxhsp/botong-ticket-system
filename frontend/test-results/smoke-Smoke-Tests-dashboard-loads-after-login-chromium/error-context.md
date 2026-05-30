# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.js >> Smoke Tests >> dashboard loads after login
- Location: e2e/smoke.spec.js:19:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[type="text"]')

```

# Page snapshot

```yaml
- generic [ref=e5]:
  - generic [ref=e6]:
    - generic [ref=e7]: 捷
    - heading "博通 Botong" [level=4] [ref=e8]
    - paragraph [ref=e9]: 售后管理系统 · 请输入访问密码
  - generic [ref=e10]:
    - generic [ref=e11]:
      - generic [ref=e12]: 访问密码
      - generic [ref=e13]:
        - textbox "访问密码" [active] [ref=e14]:
          - /placeholder: 请输入系统密码
        - button "" [ref=e15] [cursor=pointer]:
          - generic [ref=e16]: 
    - button " 进入系统" [ref=e17] [cursor=pointer]:
      - generic [ref=e18]:
        - generic [ref=e19]: 
        - text: 进入系统
  - generic [ref=e21]:
    - generic [ref=e22]: 
    - text: 仅限内部网络访问
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test'
  2  | 
  3  | test.describe('Smoke Tests', () => {
  4  |   test('login page loads', async ({ page }) => {
  5  |     await page.goto('/login')
  6  |     await expect(page).toHaveTitle(/登录/)
  7  |     await expect(page.locator('input[type="password"]')).toBeVisible()
  8  |   })
  9  | 
  10 |   test('login flow works', async ({ page }) => {
  11 |     await page.goto('/login')
  12 |     await page.fill('input[type="text"]', 'admin')
  13 |     await page.fill('input[type="password"]', 'bt780527')
  14 |     await page.click('button[type="submit"]')
  15 |     await expect(page).toHaveURL(/\//)
  16 |     await expect(page.locator('.bt-sidebar')).toBeVisible()
  17 |   })
  18 | 
  19 |   test('dashboard loads after login', async ({ page }) => {
  20 |     await page.goto('/login')
> 21 |     await page.fill('input[type="text"]', 'admin')
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  22 |     await page.fill('input[type="password"]', 'bt780527')
  23 |     await page.click('button[type="submit"]')
  24 |     await expect(page.locator('.page-dashboard')).toBeVisible()
  25 |     await expect(page.locator('.stat-value')).toHaveCount(6)
  26 |   })
  27 | 
  28 |   test('navigation menu works', async ({ page }) => {
  29 |     await page.goto('/login')
  30 |     await page.fill('input[type="text"]', 'admin')
  31 |     await page.fill('input[type="password"]', 'bt780527')
  32 |     await page.click('button[type="submit"]')
  33 | 
  34 |     await page.click('text=工单管理')
  35 |     await expect(page).toHaveURL(/\/tickets/)
  36 | 
  37 |     await page.click('text=客户管理')
  38 |     await expect(page).toHaveURL(/\/clients/)
  39 |   })
  40 | })
  41 | 
```