import { defineConfig, devices } from '@playwright/test';

/**
 * Local-only Playwright harness. Point it at a running Django dev server via
 * E2E_BASE_URL or BASE_URL (defaults to http://127.0.0.1:8000).
 *
 *   cd e2e-node
 *   npm install
 *   npm run install-browsers
 *   E2E_BASE_URL=http://127.0.0.1:8000 npm test
 *
 * Visual regression tests (`tests/visual.spec.ts`) require an authenticated
 * user — set E2E_USERNAME and E2E_PASSWORD. See README for details.
 */
export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02,
      threshold: 0.2,
      animations: 'disabled',
    },
  },
  snapshotPathTemplate: '{testDir}/__screenshots__/{testFilePath}/{arg}{ext}',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? process.env.BASE_URL ?? 'http://127.0.0.1:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    ignoreHTTPSErrors: true,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
