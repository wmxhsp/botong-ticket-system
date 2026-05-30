import { test, expect } from '@playwright/test'

test.describe('设备管理页面测试', () => {
  test('设备页面加载', async ({ page }) => {
    // 先登录
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
    
    // 访问设备页面
    await page.goto('/equipment')
    await expect(page).toHaveURL(/\/equipment/)
    
    // 验证页面加载
    await expect(page.locator('.page-equipment, .equipment-page')).toBeVisible({ timeout: 5000 })
  })
})
