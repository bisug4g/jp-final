"""
Shared Playwright fixtures for E2E tests.

Strategy
--------
* ``pytest-django``'s ``live_server`` fixture runs a Django server in-process
  against a transactional test DB. Row data is reset between tests, so we seed
  the E2E user via an autouse function-scoped fixture rather than once per
  session.
* The ``page`` fixture yields an authenticated page (fresh login each test).
  Tests that need to exercise the login screen itself should use ``anon_page``.
* The login is cheap (one form POST); for expensive workflows add targeted
  fixtures that reuse an ``authed_context`` within a test.
"""
from __future__ import annotations

import os

# pytest-playwright runs tests inside an asyncio event loop. Django's sync ORM
# refuses to run in that context unless we opt in. Must be set BEFORE Django is
# imported anywhere.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

import pytest
from django.contrib.auth import get_user_model

E2E_USERNAME = os.environ.get("E2E_USERNAME", "e2e-tester")
E2E_PASSWORD = os.environ.get("E2E_PASSWORD", "e2e-strong-password-123!")


@pytest.fixture(scope="session")
def e2e_credentials() -> dict[str, str]:
    return {"username": E2E_USERNAME, "password": E2E_PASSWORD}


@pytest.fixture(autouse=True)
def _ensure_e2e_user(transactional_db, e2e_credentials):
    """Guarantee the E2E user exists in the current test DB."""
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username=e2e_credentials["username"],
        defaults={"first_name": "E2E", "last_name": "Tester", "is_active": True},
    )
    user.set_password(e2e_credentials["password"])
    user.is_active = True
    user.save()
    return user


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Default viewport + locale for every browser context."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
        "locale": "en-IN",
        "ignore_https_errors": True,
    }


def _login(page, base_url: str, creds: dict[str, str]) -> None:
    page.goto(f"{base_url}/")
    page.fill('input[name="username"]', creds["username"])
    page.fill('input[name="password"]', creds["password"])
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard/", timeout=15_000)


@pytest.fixture
def anon_context(browser, browser_context_args):
    """Anonymous (logged-out) browser context."""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture
def anon_page(anon_context):
    page = anon_context.new_page()
    yield page
    page.close()


@pytest.fixture
def authed_context(browser, browser_context_args, live_server, e2e_credentials):
    """Browser context that has already logged in via the real UI."""
    context = browser.new_context(**browser_context_args)
    page = context.new_page()
    _login(page, live_server.url, e2e_credentials)
    page.close()
    yield context
    context.close()


@pytest.fixture
def page(authed_context, live_server):
    """Authenticated page pointed at the live Django server."""
    page = authed_context.new_page()
    page.goto(live_server.url)
    yield page
    page.close()
