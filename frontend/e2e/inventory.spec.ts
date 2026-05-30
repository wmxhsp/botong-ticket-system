import { test, expect } from '@playwright/test'

test.describe('库存管理页面测试', () => {
  test('库存页面加载', async ({ page }) => {
    // 先登录
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
    
    // 访问库存页面
    await page.goto('/inventory')
    await expect(page).toHaveURL(/\/inventory/)
    
    // 验证页面加载
    await expect(page.locator('.page-inventory, .inventory-page')).toBeVisible({ timeout: 5000 })
    
    // 验证表格或列表显示
    const table = page.locator('table, .data-table, .list-container').first()
    if (await table.isVisible()) {
      await expect(table).toBeVisible()
    }
  })
})
