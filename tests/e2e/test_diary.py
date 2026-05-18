"""Diary write flow."""
from __future__ import annotations

import uuid

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_diary_overview_loads(page: Page, live_server):
    page.goto(f"{live_server.url}/diary/")
    assert "/diary" in page.url
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_write_diary_entry(page: Page, live_server):
    marker = f"dear-diary-{uuid.uuid4().hex[:8]}"
    page.goto(f"{live_server.url}/diary/write/")
    # The diary write form uses a textarea named "content" and a hidden mood input.
    page.fill('textarea[name="content"]', f"Today I ran the E2E suite. Marker: {marker}")
    # Pick a mood if the mood picker is rendered as buttons with data-mood.
    mood_button = page.locator('[data-mood]').first
    if mood_button.count():
        mood_button.click()
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")

    # We may land on the same write page (today) or be redirected to overview;
    # either way the content should be persisted for today — re-open write page
    # and the textarea should contain our marker.
    page.goto(f"{live_server.url}/diary/write/")
    textarea = page.locator('textarea[name="content"]')
    expect(textarea).to_contain_text(marker)
