import { test, expect, Page } from '@playwright/test';

/**
 * Visual regression tests using Playwright's native screenshot comparison.
 *
 * Requirements:
 *   - A running Django server reachable at E2E_BASE_URL / BASE_URL
 *     (see playwright.config.ts — default http://127.0.0.1:8000).
 *   - Credentials for an existing user in E2E_USERNAME / E2E_PASSWORD
 *     (no defaults; tests fail fast if unset).
 *
 * Baselines live under tests/__screenshots__/visual.spec.ts/ and ARE committed.
 * Screenshots are OS-dependent — regenerate on the OS that CI uses
 * (see README for Docker Linux workflow).
 *
 * Regenerate intentionally with:
 *   npx playwright test visual.spec.ts --update-snapshots
 */

const USERNAME = process.env.E2E_USERNAME;
const PASSWORD = process.env.E2E_PASSWORD;

async function login(page: Page) {
  if (!USERNAME || !PASSWORD) {
    throw new Error('E2E_USERNAME and E2E_PASSWORD must be set for visual tests.');
  }
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.fill('input[name="username"]', USERNAME);
  await page.fill('input[name="password"]', PASSWORD);
  await Promise.all([
    page.waitForURL(/\/dashboard\/?/, { timeout: 15_000 }).catch(() => {}),
    page.click('button[type="submit"], input[type="submit"]'),
  ]);
  await page.waitForLoadState('domcontentloaded').catch(() => {});
}

/**
 * Build a list of locators that commonly host dynamic content (dates, clocks,
 * greetings). Missing elements are silently ignored by Playwright's mask.
 */
function dynamicMasks(page: Page) {
  return [
    page.locator('[data-testid="current-time"]'),
    page.locator('.timestamp'),
    page.locator('.greeting'),
    page.locator('time'),
    page.locator('[data-dynamic]'),
    page.locator('.daily-briefing'),
    page.locator('.birthday-banner'),
  ];
}

async function stabilise(page: Page) {
  // Use domcontentloaded instead of networkidle — Django pages may poll
  // background APIs that never go idle.
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  // Disable CSS animations/transitions that animations:'disabled' doesn't catch
  // (e.g., animations triggered via JS with inline styles).
  await page.addStyleTag({
    content: `*, *::before, *::after {
      animation-duration: 0s !important;
      animation-delay: 0s !important;
      transition-duration: 0s !important;
      transition-delay: 0s !important;
      caret-color: transparent !important;
    }`,
  });
  // Give late-mounted JS a moment to render without waiting for networkidle.
  await page.waitForTimeout(500);
}

test.describe('visual regression', () => {
  // Django's dev server is single-threaded; running these in parallel can
  // starve the server and cause `page.goto` timeouts. Serialize for stability.
  test.describe.configure({ mode: 'serial' });

  test('login screen (anonymous)', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await stabilise(page);
    await expect(page).toHaveScreenshot('login.png', {
      fullPage: true,
      mask: dynamicMasks(page),
    });
  });

  test.describe('authenticated', () => {
    test.beforeEach(async ({ page }) => {
      await login(page);
    });

    test('dashboard (/)', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await stabilise(page);
      await expect(page).toHaveScreenshot('dashboard.png', {
        fullPage: true,
        mask: dynamicMasks(page),
      });
    });

    test('notes', async ({ page }) => {
      await page.goto('/notes/', { waitUntil: 'domcontentloaded' });
      await stabilise(page);
      await expect(page).toHaveScreenshot('notes.png', {
        fullPage: true,
        mask: dynamicMasks(page),
      });
    });

    test('diary', async ({ page }) => {
      await page.goto('/diary/', { waitUntil: 'domcontentloaded' });
      await stabilise(page);
      await expect(page).toHaveScreenshot('diary.png', {
        fullPage: true,
        mask: dynamicMasks(page),
      });
    });

    test('goals', async ({ page }) => {
      await page.goto('/goals/', { waitUntil: 'domcontentloaded' });
      await stabilise(page);
      await expect(page).toHaveScreenshot('goals.png', {
        fullPage: true,
        mask: dynamicMasks(page),
      });
    });

    test('astro', async ({ page }) => {
      await page.goto('/astro/', { waitUntil: 'domcontentloaded' });
      await stabilise(page);
      await expect(page).toHaveScreenshot('astro.png', {
        fullPage: true,
        mask: dynamicMasks(page),
      });
    });
  });
});
