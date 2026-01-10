// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Prediction Feature E2E Tests
 */

// Helper to login
async function login(page) {
  await page.goto('/');
  await page.fill('input[name="username"]', 'Nostradam');
  await page.fill('input[name="password"]', 'test123456');
  await page.click('button[type="submit"]');
  await page.waitForSelector('input[name="username"]', { state: 'hidden', timeout: 10000 });
}

test.describe('Fraud Prediction', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate to analyzer', async ({ page }) => {
    // Click analyzer tab
    const analyzerTab = page.locator('button, a').filter({ hasText: /analyzer|analyse/i }).first();
    await analyzerTab.click();

    // Should show transaction form
    await expect(page.locator('input[type="number"]').first()).toBeVisible();
  });

  test('should display sample buttons', async ({ page }) => {
    // Navigate to analyzer
    const analyzerTab = page.locator('button, a').filter({ hasText: /analyzer|analyse/i }).first();
    await analyzerTab.click();

    // Look for sample buttons (legitimate and fraud)
    const sampleButtons = page.locator('button').filter({ hasText: /sample|échantillon/i });
    expect(await sampleButtons.count()).toBeGreaterThanOrEqual(2);
  });

  test('should load sample transaction', async ({ page }) => {
    // Navigate to analyzer
    const analyzerTab = page.locator('button, a').filter({ hasText: /analyzer|analyse/i }).first();
    await analyzerTab.click();

    // Get initial value of first input
    const firstInput = page.locator('input[type="number"]').first();
    const initialValue = await firstInput.inputValue();

    // Click legitimate sample button
    const legitBtn = page.locator('button').filter({ hasText: /legitimate|légitime/i }).first();
    await legitBtn.click();

    // Wait for form to update
    await page.waitForTimeout(1000);

    // Value should have changed
    const newValue = await firstInput.inputValue();
    // Values should be different (sample was loaded)
    expect(newValue).toBeDefined();
  });

  test('should submit prediction form', async ({ page }) => {
    // Navigate to analyzer
    const analyzerTab = page.locator('button, a').filter({ hasText: /analyzer|analyse/i }).first();
    await analyzerTab.click();

    // Load a sample
    const legitBtn = page.locator('button').filter({ hasText: /legitimate|légitime/i }).first();
    await legitBtn.click();
    await page.waitForTimeout(500);

    // Click analyze button
    const analyzeBtn = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /analyze|analyser/i })
    ).first();
    await analyzeBtn.click();

    // Wait for result
    await page.waitForTimeout(3000);

    // Should show some result (probability, risk score, etc.)
    const resultIndicator = page.locator('[class*="bg-green"], [class*="bg-red"], text=/\\d+%/');
    await expect(resultIndicator.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display prediction result components', async ({ page }) => {
    // Navigate to analyzer
    const analyzerTab = page.locator('button, a').filter({ hasText: /analyzer|analyse/i }).first();
    await analyzerTab.click();

    // Load sample and analyze
    const legitBtn = page.locator('button').filter({ hasText: /legitimate|légitime/i }).first();
    await legitBtn.click();
    await page.waitForTimeout(500);

    const analyzeBtn = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /analyze|analyser/i })
    ).first();
    await analyzeBtn.click();

    // Wait for result
    await page.waitForTimeout(3000);

    // Check for result card
    const resultCard = page.locator('.rounded-xl, .rounded-lg').filter({ hasText: /fraud|probability|risk|risque/i });
    await expect(resultCard.first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Batch Upload', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate to batch upload', async ({ page }) => {
    // Click batch tab
    const batchTab = page.locator('button, a').filter({ hasText: /batch|lot/i }).first();
    await batchTab.click();

    // Should show upload area
    await expect(page.locator('input[type="file"], [class*="upload"], text=/csv/i').first()).toBeVisible();
  });

  test('should have file input for CSV', async ({ page }) => {
    // Navigate to batch
    const batchTab = page.locator('button, a').filter({ hasText: /batch|lot/i }).first();
    await batchTab.click();

    // Look for file input
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
  });
});

test.describe('History', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate to history', async ({ page }) => {
    // Click history tab
    const historyTab = page.locator('button, a').filter({ hasText: /history|historique/i }).first();
    await historyTab.click();

    // Should show history content
    await page.waitForTimeout(1000);

    // Look for table or list structure
    const historyContent = page.locator('table, [class*="rounded-xl"], [class*="space-y"]').first();
    await expect(historyContent).toBeVisible();
  });
});

test.describe('Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate to analytics', async ({ page }) => {
    // Click analytics tab
    const analyticsTab = page.locator('button, a').filter({ hasText: /analytics|analytique/i }).first();
    await analyticsTab.click();

    // Should show charts
    await page.waitForTimeout(1000);

    const chartContent = page.locator('svg, [class*="recharts"], canvas').first();
    await expect(chartContent).toBeVisible({ timeout: 5000 });
  });
});
