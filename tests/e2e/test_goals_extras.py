"""Extended Goals flows: detail, edit, delete, board, task create/update."""
from __future__ import annotations

import datetime as dt
import time
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import OperationalError
from playwright.sync_api import Page, expect

from goals.models import Goal, Task


def _retry_db(fn, *, attempts: int = 10, delay: float = 0.25):
    """Work around transient SQLite locks from the background live_server thread."""
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return fn()
        except OperationalError as exc:
            last_exc = exc
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def _seed_goal(username: str, *, title: str | None = None) -> Goal:
    user = _retry_db(lambda: get_user_model().objects.get(username=username))
    return _retry_db(
        lambda: Goal.objects.create(
            user=user,
            title=title or f"Seed Goal {uuid.uuid4().hex[:8]}",
            description="Seeded via ORM for E2E.",
            target_date=dt.date.today() + dt.timedelta(days=60),
            role_category="digital_marketing",
            experience_level="mid",
            time_horizon="1year",
            status="active",
        )
    )


@pytest.mark.e2e
def test_goal_detail_page(page: Page, live_server, e2e_credentials):
    goal = _seed_goal(e2e_credentials["username"])
    page.goto(f"{live_server.url}/goals/{goal.pk}/")
    expect(page.get_by_role("heading", name=goal.title)).to_be_visible()


@pytest.mark.e2e
def test_goal_board_renders(page: Page, live_server):
    page.goto(f"{live_server.url}/goals/board/")
    assert "/goals/board" in page.url
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_goal_edit_updates_title(page: Page, live_server, e2e_credentials):
    goal = _seed_goal(e2e_credentials["username"])
    new_title = f"Edited {uuid.uuid4().hex[:8]}"
    new_target = (dt.date.today() + dt.timedelta(days=90)).isoformat()

    page.goto(f"{live_server.url}/goals/{goal.pk}/edit/")
    page.fill('input[name="title"]', new_title)
    page.fill('textarea[name="description"]', "Updated description.")
    page.fill('input[name="target_date"]', new_target)
    page.select_option('select[name="role_category"]', "digital_marketing")
    page.select_option('select[name="experience_level"]', "mid")
    page.select_option('select[name="time_horizon"]', "1year")
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")

    refreshed = _retry_db(lambda: Goal.objects.get(pk=goal.pk))
    assert refreshed.title == new_title


@pytest.mark.e2e
def test_goal_delete_removes_goal(page: Page, live_server, e2e_credentials):
    goal = _seed_goal(e2e_credentials["username"])

    page.goto(f"{live_server.url}/goals/{goal.pk}/delete/")
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    assert not _retry_db(lambda: Goal.objects.filter(pk=goal.pk).exists())


@pytest.mark.e2e
def test_task_create_for_goal(page: Page, live_server, e2e_credentials):
    goal = _seed_goal(e2e_credentials["username"])
    task_title = f"E2E Task {uuid.uuid4().hex[:8]}"
    due = (dt.date.today() + dt.timedelta(days=7)).isoformat()

    page.goto(f"{live_server.url}/goals/{goal.pk}/task/create/")
    page.fill('input[name="title"]', task_title)
    page.fill('textarea[name="description"]', "Work item created via E2E test.")
    page.select_option('select[name="department"]', "operations")
    page.fill('input[name="due_date"]', due)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    assert _retry_db(lambda: Task.objects.filter(goal=goal, title=task_title).exists())


@pytest.mark.e2e
def test_task_update_status(page: Page, live_server, e2e_credentials):
    goal = _seed_goal(e2e_credentials["username"])
    task = _retry_db(
        lambda: Task.objects.create(
            goal=goal,
            title="Task to update",
            description="seed",
            department="strategy",
            due_date=dt.date.today() + dt.timedelta(days=5),
            status="pending",
        )
    )

    page.goto(f"{live_server.url}/goals/task/{task.pk}/update/")
    page.select_option('select[name="status"]', "in_progress")
    # Range input: set via JS-friendly fill.
    page.evaluate(
        "document.querySelector('input[name=\"completion_percentage\"]').value = '50'"
    )
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    refreshed = _retry_db(lambda: Task.objects.get(pk=task.pk))
    assert refreshed.status == "in_progress"
