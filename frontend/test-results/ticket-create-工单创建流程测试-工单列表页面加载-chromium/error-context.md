# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ticket-create.spec.ts >> 工单创建流程测试 >> 工单列表页面加载
- Location: e2e/ticket-create.spec.ts:47:3

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
  3  | test.describe('工单创建流程测试', () => {
  4  |   test('快速创建工单', async ({ page }) => {
  5  |     // 先登录
  6  |     await page.goto('/login')
  7  |     await page.fill('input[type="text"]', 'admin')
  8  |     await page.fill('input[type="password"]', 'bt780527')
  9  |     await page.click('button[type="submit"]')
  10 |     
  11 |     // 等待登录完成
  12 |     await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
  13 |     
  14 |     // 访问快速创建页面
  15 |     await page.goto('/tickets/quick')
  16 |     await expect(page).toHaveURL(/\/tickets\/quick/)
  17 |     
  18 |     // 验证页面加载
  19 |     await expect(page.locator('.page-ticket-create')).toBeVisible({ timeout: 5000 })
  20 |     
  21 |     // 填写客户信息（使用自动补全）
  22 |     await page.fill('input[placeholder*="客户"], input[name="client"]', '测试')
  23 |     await page.waitForTimeout(500) // 等待搜索建议
  24 |     
  25 |     // 选择第一个客户选项
  26 |     const firstClient = page.locator('.client-option, [role="option"]').first()
  27 |     if (await firstClient.isVisible()) {
  28 |       await firstClient.click()
  29 |     }
  30 |     
  31 |     // 填写问题描述
  32 |     const descriptionField = page.locator('textarea[placeholder*="描述"], textarea[name="description"]').first()
  33 |     if (await descriptionField.isVisible()) {
  34 |       await descriptionField.fill('自动化测试工单 - 验证创建功能')
  35 |     }
  36 |     
  37 |     // 提交表单
  38 |     const submitButton = page.locator('button[type="submit"], button:has-text("创建"), button:has-text("提交")').first()
  39 |     if (await submitButton.isVisible()) {
  40 |       await submitButton.click()
  41 |       
  42 |       // 验证跳转回工单列表
  43 |       await expect(page).toHaveURL(/\/tickets/, { timeout: 5000 })
  44 |     }
  45 |   })
  46 | 
  47 |   test('工单列表页面加载', async ({ page }) => {
  48 |     // 登录后访问工单列表
  49 |     await page.goto('/login')
> 50 |     await page.fill('input[type="text"]', 'admin')
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  51 |     await page.fill('input[type="password"]', 'bt780527')
  52 |     await page.click('button[type="submit"]')
  53 |     
  54 |     await page.goto('/tickets')
  55 |     await expect(page).toHaveURL(/\/tickets/)
  56 |     
  57 |     // 验证列表页面加载
  58 |     await expect(page.locator('.page-tickets, .ticket-list')).toBeVisible({ timeout: 5000 })
  59 |   })
  60 | })
  61 | 
```