import { test, expect } from '@playwright/test'

test.describe('命令面板功能测试', () => {
  test('打开命令面板', async ({ page }) => {
    // 先登录
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    
    // 等待登录完成
    await expect(page.locator('.page-dashboard')).toBeVisible({ timeout: 5000 })
    
    // 使用快捷键打开命令面板（Cmd+K on Mac, Ctrl+K on Windows/Linux）
    await page.keyboard.press('Meta+K')
    
    // 验证命令面板打开
    const palette = page.locator('.command-palette, [role="dialog"]:has(.search-input)')
    await expect(palette).toBeVisible({ timeout: 3000 })
  })

  test('搜索工单', async ({ page }) => {
    // 登录后打开命令面板
    await page.goto('/')
    await page.keyboard.press('Meta+K')
    
    // 等待面板打开
    await page.waitForTimeout(500)
    
    // 输入搜索关键词
    const searchInput = page.locator('.search-input, input[placeholder*="搜索"]')
    if (await searchInput.isVisible()) {
      await searchInput.fill('测试')
      
      // 等待搜索结果
      await page.waitForTimeout(1000)
      
      // 验证有结果或显示无结果提示
      const results = page.locator('.result-item, [role="option"]')
      const resultCount = await results.count()
      
      // 至少有结果或者显示"无结果"提示
      const noResults = page.locator('.no-results, text=未找到')
      expect(resultCount > 0 || await noResults.isVisible()).toBeTruthy()
    }
  })

  test('快捷命令显示', async ({ page }) => {
    // 登录后打开命令面板（不输入搜索词）
    await page.goto('/')
    await page.keyboard.press('Meta+K')
    
    await page.waitForTimeout(500)
    
    // 验证显示常用命令或最近使用
    const commands = page.locator('.result-item, [role="option"]')
    const commandCount = await commands.count()
    
    // 应该显示一些命令选项
    expect(commandCount).toBeGreaterThan(0)
  })
})
