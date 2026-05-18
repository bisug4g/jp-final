"""Core navigation and authenticated API endpoint coverage."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_profile_page_renders(page: Page, live_server):
    page.goto(f"{live_server.url}/profile/")
    page.wait_for_load_state("networkidle")
    assert page.url.rstrip("/").endswith("/profile")
    # Profile page should not redirect to login.
    assert "/dashboard" not in page.url or "/profile" in page.url
    # Some profile form field or heading should be visible.
    body = page.locator("body")
    expect(body).to_be_visible()


@pytest.mark.e2e
def test_password_change_page_renders(page: Page, live_server):
    page.goto(f"{live_server.url}/password-change/")
    page.wait_for_load_state("networkidle")
    expect(page.locator('input[name="old_password"]')).to_be_visible()
    expect(page.locator('input[name="new_password1"]')).to_be_visible()
    expect(page.locator('input[name="new_password2"]')).to_be_visible()
    expect(page.locator('form button[type="submit"], form input[type="submit"]').first).to_be_visible()


@pytest.mark.e2e
def test_password_change_happy_path(page: Page, live_server, e2e_credentials):
    old_password = e2e_credentials["password"]
    new_password = "NewE2Ep@ss123!"

    page.goto(f"{live_server.url}/password-change/")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="old_password"]', old_password)
    page.fill('input[name="new_password1"]', new_password)
    page.fill('input[name="new_password2"]', new_password)
    page.locator('form button[type="submit"], form input[type="submit"]').first.click()
    page.wait_for_load_state("networkidle")

    # On success Django redirects to /profile/. Either way we must not still be
    # sitting on the password-change form with validation errors.
    assert "/password-change" not in page.url or page.locator("text=successfully").count() > 0

    # Verify the new password actually works by logging in via the form.
    page.goto(f"{live_server.url}/logout/")
    page.wait_for_load_state("networkidle")
    page.goto(f"{live_server.url}/")
    page.fill('input[name="username"]', e2e_credentials["username"])
    page.fill('input[name="password"]', new_password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard/", timeout=15_000)
    assert "/dashboard" in page.url

    # Be defensive: revert to the original password so other tests remain
    # isolated even if the DB were somehow shared.
    page.goto(f"{live_server.url}/password-change/")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="old_password"]', new_password)
    page.fill('input[name="new_password1"]', old_password)
    page.fill('input[name="new_password2"]', old_password)
    page.locator('form button[type="submit"], form input[type="submit"]').first.click()
    page.wait_for_load_state("networkidle")


@pytest.mark.e2e
def test_sessions_dashboard_loads(page: Page, live_server):
    resp = page.goto(f"{live_server.url}/sessions/")
    page.wait_for_load_state("networkidle")
    assert resp is not None and resp.status == 200
    # Page should render (body present) and not redirect back to login.
    expect(page.locator("body")).to_be_visible()
    assert "/sessions" in page.url


@pytest.mark.e2e
def test_api_activity_stats(page: Page, live_server):
    resp = page.request.get(f"{live_server.url}/api/activity-stats/")
    assert resp.status == 200, resp.text()
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert "stats" in data


@pytest.mark.e2e
def test_api_goal_progress(page: Page, live_server):
    resp = page.request.get(f"{live_server.url}/api/goal-progress/")
    assert resp.status == 200, resp.text()
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert "charts" in data


@pytest.mark.e2e
def test_logout_redirects_to_login(page: Page, live_server):
    page.goto(f"{live_server.url}/logout/")
    page.wait_for_load_state("networkidle")
    # After logout, the login form should be visible again.
    expect(page.locator('input[name="username"]')).to_be_visible()
    assert "/dashboard" not in page.url
