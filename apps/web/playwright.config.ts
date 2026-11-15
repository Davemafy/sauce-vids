import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 45_000,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    launchOptions: process.env.SAUCE_CHROME_BIN
      ? { executablePath: process.env.SAUCE_CHROME_BIN }
      : undefined,
    baseURL: 'http://127.0.0.1:3000',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run start',
    url: `http://127.0.0.1:3000${process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || ""}`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
