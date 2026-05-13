import { expect, test } from '@playwright/test';

test.describe.serial('SautiRelay integrated frontend workflow', () => {
  let trackingCode = '';

  test('switches, persists, and falls back for interface locales', async ({ browser, page }) => {
    await page.goto('/');
    await page.waitForFunction(() => document.documentElement.dataset.sautirelayHydrated === 'true');
    await expect(page.getByRole('heading', { name: 'Report early signs of conflict safely.' })).toBeVisible();

    await page.getByLabel('Interface language').selectOption('sw');
    await page.waitForFunction(() => document.documentElement.dataset.sautirelayHydrated === 'true');
    await expect(page.getByRole('heading', { name: 'Ripoti dalili za mapema za migogoro kwa usalama.' })).toBeVisible();
    await page.reload();
    await page.waitForFunction(() => document.documentElement.dataset.sautirelayHydrated === 'true');
    await expect(page.getByRole('heading', { name: 'Ripoti dalili za mapema za migogoro kwa usalama.' })).toBeVisible();

    await page.getByLabel('Lugha ya kiolesura').selectOption('ar');
    await page.waitForFunction(() => document.documentElement.dataset.sautirelayHydrated === 'true');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.getByRole('heading', { name: 'أبلغ بأمان عن العلامات المبكرة للنزاع.' })).toBeVisible();
    const hasHorizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    );
    expect(hasHorizontalOverflow).toBe(false);

    const fallbackContext = await browser.newContext({ locale: 'zu-ZA' });
    const fallbackPage = await fallbackContext.newPage();
    await fallbackPage.goto('/');
    await fallbackPage.waitForFunction(() => document.documentElement.dataset.sautirelayHydrated === 'true');
    await expect(fallbackPage.getByRole('heading', { name: 'Report early signs of conflict safely.' })).toBeVisible();
    await expect(fallbackPage.locator('html')).toHaveAttribute('lang', 'en');
    await fallbackContext.close();
  });

  test('submits an anonymous report and checks reporter-safe status', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Report early signs of conflict safely.' })).toBeVisible();

    await page
      .getByLabel('Tell us what happened or what you heard')
      .fill('There are rumors that youth may block herders from the water point tomorrow.');
    await page.getByLabel('Safest useful area').fill('El Fasher area');
    await page.getByLabel('Country').fill('Sudan');
    await page.getByLabel('Region / province / state').fill('Darfur');
    await page.getByLabel('People may be in immediate danger').check();
    await page.getByRole('button', { name: 'Submit safely' }).click();

    const confirmation = page.getByRole('status');
    await expect(confirmation).toContainText('Your report has been received safely.');
    await expect(confirmation).toContainText(/SR-[A-Z0-9]{5,12}/);

    const confirmationText = await confirmation.textContent();
    trackingCode = confirmationText?.match(/SR-[A-Z0-9]{5,12}/)?.[0] ?? '';
    expect(trackingCode).toMatch(/^SR-[A-Z0-9]{5,12}$/);

    await page.goto('/status');
    await page.getByPlaceholder('SR-8K42P').fill(trackingCode);
    await page.getByRole('button', { name: 'Check status' }).click();
    await expect(page.getByRole('status')).toContainText('Under review');
  });

  test('loads verifier, mediator, and analytics dashboards through the API', async ({ page }) => {
    expect(trackingCode).toMatch(/^SR-[A-Z0-9]{5,12}$/);

    await page.goto('/verifier', { waitUntil: 'networkidle' });
    await Promise.all([
      page.waitForResponse((response) => response.url().endsWith('/reports') && response.status() === 200),
      page.waitForResponse((response) => response.url().endsWith('/clusters') && response.status() === 200),
      page.getByRole('button', { name: 'Load seeded queue' }).click(),
    ]);
    await expect(page.getByLabel('Verifier queue')).toContainText('PENDING_REVIEW');
    await expect(page.getByLabel('Verifier queue')).toContainText('[RESOURCE_POINT]');

    await page.goto('/analytics', { waitUntil: 'networkidle' });
    await Promise.all([
      page.waitForResponse((response) => response.url().endsWith('/dashboard/metrics') && response.status() === 200),
      page.getByRole('button', { name: 'Load metrics' }).click(),
    ]);
    await expect(page.getByText('Total reports')).toBeVisible();
    await expect(page.getByRole('article').filter({ hasText: 'Total reports' })).toContainText(/[1-9]\d*/);

    await page.goto('/mediator', { waitUntil: 'networkidle' });
    await Promise.all([
      page.waitForResponse((response) => response.url().endsWith('/escalations') && response.status() === 200),
      page.getByRole('button', { name: 'Load assignments' }).click(),
    ]);
    await expect(page.getByRole('button', { name: 'Load assignments' })).toBeEnabled();
    await expect(page.getByRole('alert')).toHaveCount(0);
  });
});
