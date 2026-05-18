"""Deeper dashboard E2E coverage: navigation, widgets, mobile, API."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


DASHBOARD_PATH = "/dashboard/"


@pytest.mark.e2e
def test_dashboard_nav_links_present(page: Page, live_server):
    """All feature-area nav links should be in the DOM on the dashboard."""
    page.goto(f"{live_server.url}{DASHBOARD_PATH}")

    # Link hrefs come from base.html navbar. These are the feature areas.
    expected_hrefs = [
        "/notes/",
        "/diary/",
        "/goals/",
        "/astro/",
        "/ai-chat/",
        "/tangred/",
    ]
    for href in expected_hrefs:
        loc = page.locator(f'nav a[href="{href}"]')
        assert loc.count() >= 1, f"Missing nav link to {href}"


@pytest.mark.e2e
def test_dashboard_widgets_render(page: Page, live_server):
    """Each dashboard widget container should exist in the DOM."""
    page.goto(f"{live_server.url}{DASHBOARD_PATH}")

    # Structural containers defined in templates/core/dashboard.html.
    expect(page.locator(".dashboard-container")).to_be_visible()
    expect(page.locator(".welcome-header")).to_be_visible()

    # Widget containers — asserted via ID selectors. Don't check dynamic values.
    for sel in [
        "#activity-tracker",
        "#briefing-box",
        "#astro-box",
        "#moodChart",
        "#goalChart",
        "#tangred-card",
    ]:
        assert page.locator(sel).count() == 1, f"Widget {sel} missing"

    # At least a handful of enterprise cards should render.
    assert page.locator(".enterprise-card").count() >= 6


@pytest.mark.e2e
def test_dashboard_navigate_to_notes_and_back(page: Page, live_server):
    """Click the Notes nav link, verify /notes/ loads, return to dashboard."""
    page.goto(f"{live_server.url}{DASHBOARD_PATH}")

    page.locator('nav a[href="/notes/"]').first.click()
    page.wait_for_url("**/notes/", timeout=15_000)
    assert "/notes/" in page.url
    expect(page.locator("body")).to_be_visible()

    page.locator('nav a[href="/dashboard/"]').first.click()
    page.wait_for_url("**/dashboard/", timeout=15_000)
    assert "/dashboard/" in page.url
    expect(page.locator(".dashboard-container")).to_be_visible()


@pytest.mark.e2e
def test_mobile_dashboard(browser, live_server, e2e_credentials):
    """Dashboard should render on a narrow viewport without runaway horizontal overflow."""
    ctx = browser.new_context(viewport={"width": 375, "height": 667})
    try:
        p = ctx.new_page()
        p.goto(f"{live_server.url}/")
        p.fill('input[name="username"]', e2e_credentials["username"])
        p.fill('input[name="password"]', e2e_credentials["password"])
        p.click('button[type="submit"]')
        p.wait_for_url("**/dashboard/", timeout=15_000)

        expect(p.locator(".dashboard-container")).to_be_visible()

        # Either the hamburger (navbar-toggler) or a key nav item should be
        # present/visible at this viewport.
        hamburger = p.locator("button.navbar-toggler")
        assert hamburger.count() == 1
        assert hamburger.is_visible(), "Hamburger should be visible on mobile"

        # Horizontal scroll tolerance: allow a few pixels of rounding/scrollbar.
        dims = p.evaluate(
            "() => ({sw: document.documentElement.scrollWidth,"
            "        cw: document.documentElement.clientWidth})"
        )
        assert dims["sw"] - dims["cw"] <= 20, (
            f"Unexpected horizontal overflow: scrollWidth={dims['sw']} "
            f"clientWidth={dims['cw']}"
        )
    finally:
        ctx.close()


@pytest.mark.e2e
def test_daily_briefing_api(page: Page, live_server):
    """The daily briefing endpoint should respond; 200 or 503 both tolerable."""
    resp = page.request.get(f"{live_server.url}/api/daily-briefing/")
    assert resp.status in (200, 503), f"Unexpected status {resp.status}"

    payload = resp.json()
    # Both success and failure shapes include a stats object.
    assert "stats" in payload
    assert isinstance(payload["stats"], dict)
    if resp.status == 200:
        assert payload.get("success") is True
        assert "briefing" in payload
    else:
        assert payload.get("success") is False
        assert "error" in payload


@pytest.mark.e2e
def test_dashboard_filter_or_tab(page: Page, live_server):
    """If the dashboard has a tab/filter toggle, clicking it changes state.

    The current dashboard template has no explicit tabs/filters, so this test
    skips gracefully when none are found rather than asserting false behaviour.
    """
    page.goto(f"{live_server.url}{DASHBOARD_PATH}")

    candidates = page.locator(
        ".dashboard-container [role='tab'], "
        ".dashboard-container .nav-tabs button, "
        ".dashboard-container .nav-tabs a, "
        ".dashboard-container [data-bs-toggle='tab'], "
        ".dashboard-container [data-filter]"
    )
    if candidates.count() == 0:
        pytest.skip("No tab/filter toggle on dashboard template")

    first = candidates.first
    before = first.get_attribute("aria-selected") or first.get_attribute("class") or ""
    first.click()
    page.wait_for_timeout(250)
    after = first.get_attribute("aria-selected") or first.get_attribute("class") or ""
    assert before != after, "Toggle state did not change after click"
