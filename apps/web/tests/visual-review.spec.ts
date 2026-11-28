import { test, expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';

for (const [label, width, height] of [
  ['desktop', 1440, 900],
  ['mobile', 390, 844],
] as const) {
  test('private Studio visual structure at ' + label, async ({ page }) => {
    await page.route('**/api/studio/url/auth', route => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ authorized: false, configured: true }),
    }));
    await page.setViewportSize({ width, height });
    await page.goto('/studio');
    await expect(page.getByRole('heading', { name: /your product deserves/i })).toBeVisible();
    await expect(page.getByLabel('Private pilot access code')).toBeVisible();
    const measured = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
    }));
    expect(measured.content).toBeLessThanOrEqual(measured.client + 2);
    mkdirSync('artifacts', { recursive: true });
    await page.screenshot({ path: 'artifacts/studio-' + label + '.png', fullPage: true, animations: 'disabled' });
  });
}
