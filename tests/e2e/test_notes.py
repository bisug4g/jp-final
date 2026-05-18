"""Notes CRUD end-to-end."""
from __future__ import annotations

import uuid

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_notes_list_page_loads(page: Page, live_server):
    page.goto(f"{live_server.url}/notes/")
    assert "/notes" in page.url
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_create_note_flow(page: Page, live_server):
    title = f"E2E Note {uuid.uuid4().hex[:8]}"
    body = "This note was created by the Playwright E2E suite."

    page.goto(f"{live_server.url}/notes/create/")
    page.fill('input[name="title"]', title)
    page.fill('textarea[name="content"]', body)
    page.click('button[type="submit"], input[type="submit"]')

    # After submit we expect to land on the note detail or the list; either way,
    # navigating to the list must show the title.
    page.goto(f"{live_server.url}/notes/")
    expect(page.get_by_text(title)).to_be_visible()
