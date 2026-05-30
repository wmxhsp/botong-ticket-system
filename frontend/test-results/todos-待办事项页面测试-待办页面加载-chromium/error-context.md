# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: todos.spec.ts >> 待办事项页面测试 >> 待办页面加载
- Location: e2e/todos.spec.ts:4:3

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
  3  | test.describe('待办事项页面测试', () => {
  4  |   test('待办页面加载', async ({ page }) => {
  5  |     // 先登录
  6  |     await page.goto('/login')
> 7  |     await page.fill('input[type="text"]', 'admin')
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  8  |     await page.fill('input[type="password"]', 'bt780527')
  9  |     await page.click('button[type="submit"]')
  10 |     
  11 |     await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
  12 |     
  13 |     // 访问待办页面
  14 |     await page.goto('/todos')
  15 |     await expect(page).toHaveURL(/\/todos/)
  16 |     
  17 |     // 验证页面加载
  18 |     await expect(page.locator('.page-todos, .todos-page')).toBeVisible({ timeout: 5000 })
  19 |     
  20 |     // 验证今日待办或列表显示
  21 |     const todoList = page.locator('.todo-list, .todo-items, ul li').first()
  22 |     if (await todoList.isVisible()) {
  23 |       await expect(todoList).toBeVisible()
  24 |     }
  25 |   })
  26 | })
  27 | 
```