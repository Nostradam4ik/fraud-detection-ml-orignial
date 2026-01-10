// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Authentication E2E Tests
 */

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page when not authenticated', async ({ page }) => {
    // Check for login form elements (works with any language)
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.fill('input[name="username"]', 'wronguser');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.bg-red-50, .dark\\:bg-red-900\\/30')).toBeVisible({ timeout: 5000 });
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.fill('input[name="username"]', 'Nostradam');
    await page.fill('input[name="password"]', 'test123456');
    await page.click('button[type="submit"]');

    // Should show dashboard navigation items
    await expect(page.locator('[data-testid="nav-dashboard"], nav, .nav')).toBeVisible({ timeout: 10000 });
  });

  test('should persist login state on page refresh', async ({ page }) => {
    await page.fill('input[name="username"]', 'Nostradam');
    await page.fill('input[name="password"]', 'test123456');
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForTimeout(2000);

    // Refresh page
    await page.reload();

    // Should still show main app (not login form)
    await expect(page.locator('input[name="username"]')).not.toBeVisible({ timeout: 5000 });
  });
});

test.describe('Registration', () => {
  test('should navigate to registration form', async ({ page }) => {
    await page.goto('/');

    // Click on the sign up link (look for text containing "sign up" or registration link)
    const signUpLink = page.getByRole('button', { name: /sign up/i }).or(
      page.getByText(/sign up/i)
    );
    await signUpLink.click();

    // Should show email field which is only in registration form
    await expect(page.locator('input[name="email"]')).toBeVisible();
  });

  test('should show full_name field in registration', async ({ page }) => {
    await page.goto('/');

    // Navigate to registration
    const signUpLink = page.getByRole('button', { name: /sign up/i }).or(
      page.getByText(/sign up/i)
    );
    await signUpLink.click();

    // Should show full name field
    await expect(page.locator('input[name="full_name"]')).toBeVisible();
  });
});

test.describe('Forgot Password', () => {
  test('should navigate to forgot password form', async ({ page }) => {
    await page.goto('/');

    // Click forgot password link
    const forgotLink = page.getByRole('button', { name: /forgot/i }).or(
      page.getByText(/forgot/i)
    );
    await forgotLink.click();

    // Should show email field only (no username)
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="username"]')).not.toBeVisible();
  });
});
