import { expect, test } from '@playwright/test';

test('a product URL from the homepage reaches the real private studio without leaking its query', async ({ page }) => {
  await page.route('**/api/studio/url/auth', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ authorized: false, configured: true }),
  }));
  await page.goto('/');
  await page.getByRole('textbox', { name: /got a product\? start here/i })
    .fill('https://example.com/dashboard?access_token=should-not-travel#settings');
  await page.getByRole('button', { name: /take a look/i }).click();

  await expect(page).toHaveURL(/\/studio\?url=/);
  await expect(page.getByLabel('Product website')).toHaveValue('https://example.com/dashboard');
  await expect(page.getByLabel('Private pilot access code')).toBeVisible();
  await expect(page.getByRole('button', { name: /make film/i })).toBeDisabled();
  await expect(page.getByRole('region', { name: 'Live URL film production status' })).toHaveCount(0);
  expect(page.url()).not.toContain('access_token');
});

test('invalid product URLs stay on the homepage and show a real error', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('textbox', { name: /got a product\? start here/i }).fill('http://localhost');
  await page.getByRole('button', { name: /take a look/i }).click();
  await expect(page.locator('#try-url-error')).toContainText(/public website address/i);
  await expect(page).toHaveURL('/');
});
