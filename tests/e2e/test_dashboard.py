"""Dashboard & top-level navigation smoke tests."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_loads_after_login(page: Page, live_server):
    page.goto(f"{live_server.url}/dashboard/")
    assert "/dashboard" in page.url
    # Dashboard body should exist (no 500 page).
    expect(page.locator("body")).to_be_visible()
    # We should not see the login form.
    assert page.locator('input[name="password"]').count() == 0


@pytest.mark.e2e
def test_profile_page_accessible(page: Page, live_server):
    page.goto(f"{live_server.url}/profile/")
    assert page.url.endswith("/profile/")
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_health_endpoint_public(anon_page: Page, live_server):
    """Health check must work without authentication (K8s probe)."""
    response = anon_page.request.get(f"{live_server.url}/health")
    assert response.status == 200
    payload = response.json()
    assert payload["status"] == "healthy"
