"""Login / logout flows."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_login_page_renders(anon_page: Page, live_server):
    anon_page.goto(live_server.url)
    expect(anon_page.locator('input[name="username"]')).to_be_visible()
    expect(anon_page.locator('input[name="password"]')).to_be_visible()
    expect(anon_page.locator('button[type="submit"]')).to_be_visible()


@pytest.mark.e2e
def test_login_with_valid_credentials(anon_page: Page, live_server, e2e_credentials):
    anon_page.goto(live_server.url)
    anon_page.fill('input[name="username"]', e2e_credentials["username"])
    anon_page.fill('input[name="password"]', e2e_credentials["password"])
    anon_page.click('button[type="submit"]')
    anon_page.wait_for_url("**/dashboard/", timeout=15_000)
    assert "/dashboard" in anon_page.url


@pytest.mark.e2e
def test_login_rejects_invalid_credentials(anon_page: Page, live_server):
    anon_page.goto(live_server.url)
    anon_page.fill('input[name="username"]', "definitely-not-a-user")
    anon_page.fill('input[name="password"]', "wrong-password")
    anon_page.click('button[type="submit"]')
    # Still on the login page (no redirect to dashboard).
    anon_page.wait_for_load_state("networkidle")
    assert "/dashboard" not in anon_page.url
    expect(anon_page.locator('input[name="username"]')).to_be_visible()


@pytest.mark.e2e
def test_logout_returns_to_login(page: Page, live_server):
    page.goto(f"{live_server.url}/logout/")
    page.wait_for_load_state("networkidle")
    # Back on login page → username field visible again.
    expect(page.locator('input[name="username"]')).to_be_visible()
    assert "/dashboard" not in page.url
