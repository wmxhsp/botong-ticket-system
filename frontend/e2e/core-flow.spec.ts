import { test, expect } from '@playwright/test'

test.describe('核心流程测试', () => {
  test('登录并查看仪表盘', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveTitle(/登录/)
    
    // 输入凭据
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    // 验证跳转到首页
    await expect(page).toHaveURL(/\//)
    
    // 验证仪表盘内容加载
    await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
    
    // 验证统计数据卡片显示（应该有6个统计项）
    const statValues = page.locator('.stat-value')
    await expect(statValues).toHaveCount(6)
  })

  test('导航菜单功能', async ({ page }) => {
    // 先登录
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    // 等待登录完成
    await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
    
    // 测试工单管理导航
    await page.click('text=工单管理')
    await expect(page).toHaveURL(/\/tickets/)
    
    // 测试客户管理导航
    await page.click('text=客户管理')
    await expect(page).toHaveURL(/\/clients/)
  })
})
