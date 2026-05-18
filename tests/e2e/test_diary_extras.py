"""Extra diary E2E coverage: calendar, summary, entry detail, dated write."""
from __future__ import annotations

import datetime as dt
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from playwright.sync_api import Page, expect

from diary.models import DiaryEntry


@pytest.mark.e2e
def test_diary_calendar_loads(page: Page, live_server):
    page.goto(f"{live_server.url}/diary/calendar/")
    assert "/diary/calendar" in page.url
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_diary_summary_loads(page: Page, live_server):
    page.goto(f"{live_server.url}/diary/summary/")
    assert "/diary/summary" in page.url
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_diary_entry_detail_from_seed(page: Page, live_server, e2e_credentials):
    User = get_user_model()
    user = User.objects.get(username=e2e_credentials["username"])
    marker = f"seed-entry-{uuid.uuid4().hex[:8]}"
    # Use a past date to avoid collision with unique_together on today's entry
    # and to sidestep the write-view redirect semantics.
    past_date = timezone.now().date() - dt.timedelta(days=3)
    entry = DiaryEntry.objects.create(
        user=user,
        entry_date=past_date,
        content=f"This is the seeded diary body. Marker: {marker}",
        input_method="type",
        mood=4,
    )

    page.goto(f"{live_server.url}/diary/entry/{entry.pk}/")
    expect(page.locator("body")).to_contain_text(marker)


@pytest.mark.e2e
def test_diary_write_for_today_date_url(page: Page, live_server, e2e_credentials):
    """The dated write URL only accepts today's date; other dates redirect to overview."""
    User = get_user_model()
    user = User.objects.get(username=e2e_credentials["username"])
    today = timezone.now().date()
    marker = f"dated-write-{uuid.uuid4().hex[:8]}"

    page.goto(f"{live_server.url}/diary/write/{today.isoformat()}/")
    page.fill('textarea[name="content"]', f"Entry for {today}. Marker: {marker}")
    mood_button = page.locator('[data-mood]').first
    if mood_button.count():
        mood_button.click()
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")

    # View resolves to diary_entry_detail after save.
    entry = DiaryEntry.objects.filter(user=user, entry_date=today).first()
    assert entry is not None, "Entry should have been persisted for today"
    assert marker in entry.content
    assert f"/diary/entry/{entry.pk}" in page.url


@pytest.mark.e2e
def test_diary_calendar_requires_login(anon_page: Page, live_server):
    target = f"{live_server.url}/diary/calendar/"
    anon_page.goto(target)
    anon_page.wait_for_load_state("networkidle")
    # Should be redirected away from the protected page to the login flow.
    assert "/diary/calendar" not in anon_page.url or "next=" in anon_page.url
    # Login page renders a username field.
    expect(anon_page.locator('input[name="username"]')).to_be_visible()
