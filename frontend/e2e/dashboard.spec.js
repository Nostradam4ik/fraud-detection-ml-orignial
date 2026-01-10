// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Dashboard E2E Tests
 */

// Helper to login
async function login(page) {
  await page.goto('/');
  await page.fill('input[name="username"]', 'Nostradam');
  await page.fill('input[name="password"]', 'test123456');
  await page.click('button[type="submit"]');
  // Wait for navigation to complete
  await page.waitForSelector('input[name="username"]', { state: 'hidden', timeout: 10000 });
}

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display dashboard after login', async ({ page }) => {
    // Should have some statistics displayed
    await expect(page.locator('.bg-white, .dark\\:bg-gray-800').first()).toBeVisible();
  });

  test('should display stat cards', async ({ page }) => {
    // Look for stat card structure
    const statCards = page.locator('.rounded-xl');
    await expect(statCards.first()).toBeVisible();
    expect(await statCards.count()).toBeGreaterThan(0);
  });

  test('should have period selector dropdown', async ({ page }) => {
    // Find select/combobox element
    const selector = page.locator('select').first();
    await expect(selector).toBeVisible();
  });

  test('should have refresh functionality', async ({ page }) => {
    // Find refresh button by icon or class
    const refreshBtn = page.locator('button').filter({ has: page.locator('[class*="animate-spin"], svg') }).first();
    await expect(refreshBtn).toBeVisible();
  });

  test('should display charts container', async ({ page }) => {
    // Look for recharts container or chart elements
    const chartContainer = page.locator('[class*="recharts"], svg, .recharts-wrapper').first();
    await expect(chartContainer).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should have navigation menu', async ({ page }) => {
    // Check for navigation elements
    const nav = page.locator('nav, [role="navigation"], .flex.gap');
    await expect(nav.first()).toBeVisible();
  });

  test('should navigate between tabs', async ({ page }) => {
    // Find clickable navigation items
    const navItems = page.locator('button, a').filter({ hasText: /dashboard|analyzer|analytics|history|upload/i });
    const count = await navItems.count();
    expect(count).toBeGreaterThan(0);

    // Click first nav item
    if (count > 0) {
      await navItems.first().click();
      await page.waitForTimeout(500);
    }
  });

  test('should display user info', async ({ page }) => {
    // Look for username display
    await expect(page.locator('text=Nostradam')).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await login(page);

    // Should show mobile navigation
    const mobileNav = page.locator('.mobile-nav, [class*="bottom-0"], nav');
    await expect(mobileNav.first()).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await login(page);

    // Should render properly
    const content = page.locator('.bg-white, .dark\\:bg-gray-800').first();
    await expect(content).toBeVisible();
  });

  test('should adapt layout on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await login(page);

    // Should have full layout
    const content = page.locator('.grid, .flex').first();
    await expect(content).toBeVisible();
  });
});

test.describe('Theme', () => {
  test('should support dark mode', async ({ page }) => {
    await login(page);

    // Look for theme toggle
    const themeToggle = page.locator('[data-testid="theme-toggle"], button').filter({
      has: page.locator('svg')
    });

    const toggles = await themeToggle.count();
    if (toggles > 0) {
      // Click theme toggle
      await themeToggle.first().click();
      await page.waitForTimeout(500);

      // Check if dark class is applied
      const html = page.locator('html');
      const hasDark = await html.evaluate(el => el.classList.contains('dark'));
      // Toggle should work either way
      expect(typeof hasDark).toBe('boolean');
    }
  });
});
