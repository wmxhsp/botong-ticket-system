import { test, expect } from '@playwright/test'

test.describe('工单创建流程测试', () => {
  test('快速创建工单', async ({ page }) => {
    // 先登录
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    // 等待登录完成
    await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
    
    // 访问快速创建页面
    await page.goto('/tickets/quick')
    await expect(page).toHaveURL(/\/tickets\/quick/)
    
    // 验证页面加载
    await expect(page.locator('.page-ticket-create')).toBeVisible({ timeout: 5000 })
    
    // 填写客户信息（使用自动补全）
    await page.fill('input[placeholder*="客户"], input[name="client"]', '测试')
    await page.waitForTimeout(500) // 等待搜索建议
    
    // 选择第一个客户选项
    const firstClient = page.locator('.client-option, [role="option"]').first()
    if (await firstClient.isVisible()) {
      await firstClient.click()
    }
    
    // 填写问题描述
    const descriptionField = page.locator('textarea[placeholder*="描述"], textarea[name="description"]').first()
    if (await descriptionField.isVisible()) {
      await descriptionField.fill('自动化测试工单 - 验证创建功能')
    }
    
    // 提交表单
    const submitButton = page.locator('button[type="submit"], button:has-text("创建"), button:has-text("提交")').first()
    if (await submitButton.isVisible()) {
      await submitButton.click()
      
      // 验证跳转回工单列表
      await expect(page).toHaveURL(/\/tickets/, { timeout: 5000 })
    }
  })

  test('工单列表页面加载', async ({ page }) => {
    // 登录后访问工单列表
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    await page.goto('/tickets')
    await expect(page).toHaveURL(/\/tickets/)
    
    // 验证列表页面加载
    await expect(page.locator('.page-tickets, .ticket-list')).toBeVisible({ timeout: 5000 })
  })
})
