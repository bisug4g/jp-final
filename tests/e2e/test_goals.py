"""Goals creation flow."""
from __future__ import annotations

import datetime as dt
import uuid

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_goals_list_loads(page: Page, live_server):
    page.goto(f"{live_server.url}/goals/")
    assert "/goals" in page.url
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_create_goal_flow(page: Page, live_server):
    title = f"E2E Goal {uuid.uuid4().hex[:8]}"
    target = (dt.date.today() + dt.timedelta(days=30)).isoformat()

    page.goto(f"{live_server.url}/goals/create/")
    page.select_option('select[name="role_category"]', "digital_marketing")
    page.select_option('select[name="experience_level"]', "mid")
    page.select_option('select[name="time_horizon"]', "1year")
    page.fill('input[name="title"]', title)
    page.fill('textarea[name="description"]', "Ship the E2E test suite.")
    page.fill('input[name="target_date"]', target)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")

    page.goto(f"{live_server.url}/goals/")
    expect(page.get_by_text(title)).to_be_visible()
