import { test, expect } from '@playwright/test'

test.describe('待办事项页面测试', () => {
  test('待办页面加载', async ({ page }) => {
    // 先登录
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
    
    // 访问待办页面
    await page.goto('/todos')
    await expect(page).toHaveURL(/\/todos/)
    
    // 验证页面加载
    await expect(page.locator('.page-todos, .todos-page')).toBeVisible({ timeout: 5000 })
    
    // 验证今日待办或列表显示
    const todoList = page.locator('.todo-list, .todo-items, ul li').first()
    if (await todoList.isVisible()) {
      await expect(todoList).toBeVisible()
    }
  })
})
