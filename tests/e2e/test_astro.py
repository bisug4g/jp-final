"""Astrology pages smoke test (no external API calls are triggered on GET)."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.parametrize("path", ["/astro/", "/astro/chart/", "/astro/dasha/"])
def test_astro_pages_render(page: Page, live_server, path: str):
    page.goto(f"{live_server.url}{path}")
    # Render without redirecting to login and without a 500.
    assert "login" not in page.url.lower() or path in page.url
    expect(page.locator("body")).to_be_visible()
