# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: core-flow.spec.ts >> 核心流程测试 >> 登录并查看仪表盘
- Location: e2e/core-flow.spec.ts:4:3

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
  3  | test.describe('核心流程测试', () => {
  4  |   test('登录并查看仪表盘', async ({ page }) => {
  5  |     await page.goto('/login')
  6  |     await expect(page).toHaveTitle(/登录/)
  7  |     
  8  |     // 输入凭据
> 9  |     await page.fill('input[type="text"]', 'admin')
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  10 |     await page.fill('input[type="password"]', 'bt780527')
  11 |     await page.click('button[type="submit"]')
  12 |     
  13 |     // 验证跳转到首页
  14 |     await expect(page).toHaveURL(/\//)
  15 |     
  16 |     // 验证仪表盘内容加载
  17 |     await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
  18 |     
  19 |     // 验证统计数据卡片显示（应该有6个统计项）
  20 |     const statValues = page.locator('.stat-value')
  21 |     await expect(statValues).toHaveCount(6)
  22 |   })
  23 | 
  24 |   test('导航菜单功能', async ({ page }) => {
  25 |     // 先登录
  26 |     await page.goto('/login')
  27 |     await page.fill('input[type="text"]', 'admin')
  28 |     await page.fill('input[type="password"]', 'bt780527')
  29 |     await page.click('button[type="submit"]')
  30 |     
  31 |     // 等待登录完成
  32 |     await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
  33 |     
  34 |     // 测试工单管理导航
  35 |     await page.click('text=工单管理')
  36 |     await expect(page).toHaveURL(/\/tickets/)
  37 |     
  38 |     // 测试客户管理导航
  39 |     await page.click('text=客户管理')
  40 |     await expect(page).toHaveURL(/\/clients/)
  41 |   })
  42 | })
  43 | 
```