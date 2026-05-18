import { test, expect, request as playwrightRequest } from '@playwright/test';

/**
 * Production smoke tests — read-only checks against live prod.
 *
 * These tests perform NO writes, NO logins, NO mutations. They verify that
 * the public surface of https://jaytibirthday.in is reachable, returns the
 * expected status codes, and enforces anonymous redirects.
 *
 * Run locally:
 *   BASE_URL=https://jaytibirthday.in npx playwright test prod-smoke.spec.ts
 */

const PROD_URL = process.env.BASE_URL ?? process.env.E2E_BASE_URL ?? 'https://jaytibirthday.in';

test.describe('prod smoke @prod', () => {
  test('GET /health returns 200 with {status: healthy}', async () => {
    const ctx = await playwrightRequest.newContext({ baseURL: PROD_URL });
    const res = await ctx.fetch('/health');
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('healthy');
    await ctx.dispose();
  });

  test('GET /health responds in under 2000ms', async () => {
    const ctx = await playwrightRequest.newContext({ baseURL: PROD_URL });
    const start = Date.now();
    const res = await ctx.fetch('/health');
    const elapsed = Date.now() - start;
    expect(res.status()).toBe(200);
    expect(elapsed).toBeLessThan(2000);
    await ctx.dispose();
  });

  test('GET / renders login page with username and password fields', async ({ page }) => {
    await page.goto(PROD_URL + '/');
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('GET /notes/ redirects anonymous user to login', async ({ page }) => {
    const res = await page.goto(PROD_URL + '/notes/');
    expect(res?.status()).toBe(200);
    expect(page.url()).toContain('next=');
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('GET /tangred/ redirects anonymous user to login', async ({ page }) => {
    const res = await page.goto(PROD_URL + '/tangred/');
    expect(res?.status()).toBe(200);
    expect(page.url()).toContain('next=');
    await expect(page.locator('input[name="username"]')).toBeVisible();
  });

  test('GET /robots.txt returns 200 text', async () => {
    const ctx = await playwrightRequest.newContext({ baseURL: PROD_URL });
    const res = await ctx.fetch('/robots.txt');
    expect(res.status()).toBe(200);
    const body = await res.text();
    expect(body.length).toBeGreaterThan(0);
    await ctx.dispose();
  });

  test('HTTPS cert is valid (any 200 over HTTPS confirms cert)', async () => {
    expect(PROD_URL.startsWith('https://')).toBe(true);
    const ctx = await playwrightRequest.newContext({
      baseURL: PROD_URL,
      ignoreHTTPSErrors: false,
    });
    const res = await ctx.fetch('/health');
    expect(res.status()).toBe(200);
    await ctx.dispose();
  });
});
