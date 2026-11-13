import { expect, test, type Page } from '@playwright/test';
import { mkdirSync } from 'node:fs';

async function ensureNoHorizontalOverflow(page: Page) {
  const width = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth,
  }));
  expect(width.content, `Horizontal overflow: ${JSON.stringify(width)}`).toBeLessThanOrEqual(width.viewport + 2);
}

test('desktop campaign has readable hero and a real waitlist form', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await page.evaluate(() => document.fonts.ready);
  await expect(page.getByRole('heading', { name: /make software worth watching/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /join the waitlist/i })).toHaveCount(2);
  await ensureNoHorizontalOverflow(page);
  mkdirSync('artifacts', { recursive: true });
  await page.screenshot({ path: 'artifacts/desktop.png', animations: 'disabled', fullPage: true });
});

test('mobile campaign is usable without clipping or fake success', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.evaluate(() => document.fonts.ready);
  await expect(page.getByRole('heading', { name: /make software worth watching/i })).toBeVisible();
  await ensureNoHorizontalOverflow(page);
  await page.getByText('Menu', { exact: true }).click();
  await expect(page.getByRole('navigation', { name: 'Mobile navigation' })).toBeVisible();
  await page.getByText('Menu', { exact: true }).click();
  mkdirSync('artifacts', { recursive: true });
  await page.screenshot({ path: 'artifacts/mobile.png', animations: 'disabled', fullPage: true });

  const email = page.getByRole('textbox', { name: 'Email address' }).first();
  await email.fill('visitor@example.com');
  await page.getByRole('button', { name: /join the waitlist/i }).first().click();
  // CI intentionally runs without database credentials. It must fail closed.
  await expect(page.locator('#waitlist-message-hero')).toContainText(/temporarily unavailable/i);
});

test('unconfigured persistence must not claim a successful signup', async ({ request }) => {
  const response = await request.post('/api/waitlist', {
    data: { email: 'test@example.com', source: 'hero' },
    headers: { Origin: 'http://127.0.0.1:3000' },
  });
  expect(response.status()).toBe(503);
  expect((await response.json()).ok).toBe(false);
});
