"""E2E tests for error pages and auth-gated URLs."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_404_page_renders(anon_page: Page, live_server):
    response = anon_page.goto(
        f"{live_server.url}/does-not-exist-xyz-123/",
        wait_until="domcontentloaded",
    )
    assert response is not None
    assert response.status == 404
    body = anon_page.content().lower()
    # Either our custom template or Django's DEBUG technical 404 page.
    assert (
        "page not found" in body
        or "404" in body
        or "not found" in body
    )


@pytest.mark.e2e
def test_protected_url_redirects_when_logged_out(anon_page: Page, live_server):
    anon_page.goto(f"{live_server.url}/notes/", wait_until="domcontentloaded")
    anon_page.wait_for_load_state("networkidle")
    url = anon_page.url
    assert "next=/notes/" in url or anon_page.locator('input[name="username"]').is_visible()


@pytest.mark.e2e
def test_logout_then_access_protected(page: Page, live_server):
    page.goto(f"{live_server.url}/logout/")
    page.wait_for_load_state("networkidle")
    page.goto(f"{live_server.url}/notes/", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    expect(page.locator('input[name="username"]')).to_be_visible()


@pytest.mark.e2e
def test_admin_requires_staff(page: Page, live_server):
    # Use the request context so we don't download all admin assets — the
    # Django admin can trigger ERR_INSUFFICIENT_RESOURCES during full nav.
    response = page.request.get(f"{live_server.url}/admin/")
    assert response.status == 200
    assert "/admin/login/" in response.url


@pytest.mark.e2e
def test_unknown_api_endpoint_returns_json_404(page: Page, live_server):
    # The app routes `/api/` (and `/api`) to a JSON 404 handler.
    response = page.request.get(f"{live_server.url}/api/")
    assert response.status == 404
    content_type = (response.headers.get("content-type") or "").lower()
    assert "application/json" in content_type
    payload = response.json()
    assert "error" in payload or "message" in payload
