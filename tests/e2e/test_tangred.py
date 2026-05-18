"""Tangred (wardrobe sessions + Tan Studio) end-to-end render smoke tests.

The actual create endpoints (`sessions/create/`, `studio/projects/create/`) are
POST-only and fan out to external services (Firebase, OpenAI, Stitch), so these
tests stay on GET/render assertions and never submit the forms.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_tangred_home_renders(page: Page, live_server):
    page.goto(f"{live_server.url}/tangred/")
    assert "/tangred" in page.url
    expect(page.locator("h1")).to_contain_text("Tangred")
    # The session-create form is embedded on the home page.
    expect(page.locator('form[action*="/tangred/sessions/create/"]')).to_be_visible()


@pytest.mark.e2e
def test_tangred_session_create_form_fields_visible(page: Page, live_server):
    page.goto(f"{live_server.url}/tangred/")
    form = page.locator('form[action*="/tangred/sessions/create/"]')
    expect(form).to_be_visible()
    expect(form.locator('input[name="title"]')).to_be_visible()
    expect(form.locator('input[name="photos"]')).to_be_attached()
    expect(form.locator('textarea[name="style_goal"]')).to_be_visible()
    expect(form.locator('button[type="submit"], input[type="submit"]').first).to_be_visible()


@pytest.mark.e2e
def test_tan_studio_home_renders(page: Page, live_server):
    page.goto(f"{live_server.url}/tangred/studio/")
    assert "/tangred/studio" in page.url
    expect(page.locator("h1")).to_contain_text("Tan Studio")
    expect(page.locator('form[action*="/tangred/studio/projects/create/"]')).to_be_visible()


@pytest.mark.e2e
def test_tan_studio_project_create_form_fields_visible(page: Page, live_server):
    page.goto(f"{live_server.url}/tangred/studio/")
    form = page.locator('form[action*="/tangred/studio/projects/create/"]')
    expect(form).to_be_visible()
    expect(form.locator('input[name="title"]')).to_be_visible()
    expect(form.locator('textarea[name="description"]')).to_be_visible()
    expect(form.locator('button[type="submit"], input[type="submit"]').first).to_be_visible()


@pytest.mark.e2e
def test_tangred_requires_authentication(anon_page: Page, live_server):
    anon_page.goto(f"{live_server.url}/tangred/")
    anon_page.wait_for_load_state("networkidle")
    # login_required should bounce us to the login page (root "?next=/tangred/").
    from urllib.parse import urlparse
    assert urlparse(anon_page.url).path != "/tangred/"
    expect(anon_page.locator('input[name="username"]')).to_be_visible()
    expect(anon_page.locator('input[name="password"]')).to_be_visible()
