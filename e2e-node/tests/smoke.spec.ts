import { test, expect } from '@playwright/test';

test('health endpoint returns healthy', async ({ request, baseURL }) => {
  const res = await request.get(`${baseURL}/health`);
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body.status).toBe('healthy');
});

test('login page renders', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('input[name="username"]')).toBeVisible();
  await expect(page.locator('input[name="password"]')).toBeVisible();
});
