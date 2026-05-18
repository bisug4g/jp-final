"""Extra Notes E2E coverage: detail, edit, delete, folder create/delete."""
from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from notes.models import Note, NoteFolder


def _get_user():
    return get_user_model().objects.get(username="e2e-tester")


def _csrf_from(page: Page, url: str) -> str:
    page.goto(url)
    return page.locator('input[name="csrfmiddlewaretoken"]').first.get_attribute("value")


@pytest.mark.e2e
def test_note_detail_page_shows_title(page: Page, live_server):
    user = _get_user()
    title = f"Detail Note {uuid.uuid4().hex[:8]}"
    note = Note.objects.create(user=user, title=title, content="Hello detail.")

    page.goto(f"{live_server.url}/notes/{note.pk}/")
    expect(page.get_by_text(title).first).to_be_visible()


@pytest.mark.e2e
def test_edit_note_updates_title(page: Page, live_server):
    user = _get_user()
    original = f"Original {uuid.uuid4().hex[:8]}"
    updated = f"Updated {uuid.uuid4().hex[:8]}"
    note = Note.objects.create(user=user, title=original, content="body")

    page.goto(f"{live_server.url}/notes/{note.pk}/edit/")
    page.fill('input[name="title"]', updated)
    page.click('button[type="submit"], input[type="submit"]')

    page.goto(f"{live_server.url}/notes/")
    expect(page.get_by_text(updated)).to_be_visible()

    note.refresh_from_db()
    assert note.title == updated


@pytest.mark.e2e
def test_delete_note_removes_from_list(page: Page, live_server):
    user = _get_user()
    title = f"Doomed {uuid.uuid4().hex[:8]}"
    note = Note.objects.create(user=user, title=title, content="bye")

    # Navigate to confirm-delete page (has a CSRF-protected POST form) and submit.
    page.goto(f"{live_server.url}/notes/{note.pk}/delete/")
    page.click('button[type="submit"]')
    page.wait_for_url("**/notes/")

    assert not Note.objects.filter(pk=note.pk).exists()
    expect(page.get_by_text(title)).to_have_count(0)


@pytest.mark.e2e
def test_folder_create_via_post_shows_in_list(page: Page, live_server):
    user = _get_user()
    folder_name = f"Folder {uuid.uuid4().hex[:8]}"

    # The notes list page hosts the create-folder form, so grab CSRF from there.
    token = _csrf_from(page, f"{live_server.url}/notes/")
    resp = page.request.post(
        f"{live_server.url}/notes/folder/create/",
        form={
            "csrfmiddlewaretoken": token,
            "name": folder_name,
            "icon": "📁",
            "color": "#E3F2FD",
        },
        headers={"Referer": f"{live_server.url}/notes/"},
    )
    assert resp.ok, resp.status

    assert NoteFolder.objects.filter(user=user, name=folder_name).exists()

    page.goto(f"{live_server.url}/notes/")
    expect(page.get_by_text(folder_name)).to_be_visible()


@pytest.mark.e2e
def test_folder_delete_removes_folder(page: Page, live_server):
    user = _get_user()
    folder_name = f"DelFolder {uuid.uuid4().hex[:8]}"
    folder = NoteFolder.objects.create(user=user, name=folder_name)

    page.goto(f"{live_server.url}/notes/folder/{folder.pk}/delete/")
    page.click('button[type="submit"]')
    page.wait_for_url("**/notes/")

    assert not NoteFolder.objects.filter(pk=folder.pk).exists()
    # The folder is deleted; ensure no sidebar folder link for it remains.
    # (A flash message may echo the name elsewhere on the page.)
    page.goto(f"{live_server.url}/notes/")
    expect(page.locator(f".folder-item:has-text('{folder_name}')")).to_have_count(0)
