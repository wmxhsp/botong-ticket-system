# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: command-palette.spec.ts >> 命令面板功能测试 >> 打开命令面板
- Location: e2e/command-palette.spec.ts:4:3

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
  3  | test.describe('命令面板功能测试', () => {
  4  |   test('打开命令面板', async ({ page }) => {
  5  |     // 先登录
  6  |     await page.goto('/login')
> 7  |     await page.fill('input[type="text"]', 'admin')
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  8  |     await page.fill('input[type="password"]', 'bt780527')
  9  |     await page.click('button[type="submit"]')
  10 |     
  11 |     // 等待登录完成
  12 |     await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
  13 |     
  14 |     // 使用快捷键打开命令面板（Cmd+K on Mac, Ctrl+K on Windows/Linux）
  15 |     await page.keyboard.press('Meta+K')
  16 |     
  17 |     // 验证命令面板打开
  18 |     const palette = page.locator('.command-palette, [role="dialog"]:has(.search-input)')
  19 |     await expect(palette).toBeVisible({ timeout: 3000 })
  20 |   })
  21 | 
  22 |   test('搜索工单', async ({ page }) => {
  23 |     // 登录后打开命令面板
  24 |     await page.goto('/')
  25 |     await page.keyboard.press('Meta+K')
  26 |     
  27 |     // 等待面板打开
  28 |     await page.waitForTimeout(500)
  29 |     
  30 |     // 输入搜索关键词
  31 |     const searchInput = page.locator('.search-input, input[placeholder*="搜索"]')
  32 |     if (await searchInput.isVisible()) {
  33 |       await searchInput.fill('测试')
  34 |       
  35 |       // 等待搜索结果
  36 |       await page.waitForTimeout(1000)
  37 |       
  38 |       // 验证有结果或显示无结果提示
  39 |       const results = page.locator('.result-item, [role="option"]')
  40 |       const resultCount = await results.count()
  41 |       
  42 |       // 至少有结果或者显示"无结果"提示
  43 |       const noResults = page.locator('.no-results, text=未找到')
  44 |       expect(resultCount > 0 || await noResults.isVisible()).toBeTruthy()
  45 |     }
  46 |   })
  47 | 
  48 |   test('快捷命令显示', async ({ page }) => {
  49 |     // 登录后打开命令面板（不输入搜索词）
  50 |     await page.goto('/')
  51 |     await page.keyboard.press('Meta+K')
  52 |     
  53 |     await page.waitForTimeout(500)
  54 |     
  55 |     // 验证显示常用命令或最近使用
  56 |     const commands = page.locator('.result-item, [role="option"]')
  57 |     const commandCount = await commands.count()
  58 |     
  59 |     // 应该显示一些命令选项
  60 |     expect(commandCount).toBeGreaterThan(0)
  61 |   })
  62 | })
  63 | 
```