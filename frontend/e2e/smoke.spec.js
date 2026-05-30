import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveTitle(/登录/)
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })

  test('login flow works', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\//)
    await expect(page.locator('.bt-sidebar')).toBeVisible()
  })

  test('dashboard loads after login', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')
    await expect(page.locator('.page-dashboard')).toBeVisible()
    await expect(page.locator('.stat-value')).toHaveCount(6)
  })

  test('navigation menu works', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'bt780527')
    await page.click('button[type="submit"]')

    await page.click('text=工单管理')
    await expect(page).toHaveURL(/\/tickets/)

    await page.click('text=客户管理')
    await expect(page).toHaveURL(/\/clients/)
  })
})
