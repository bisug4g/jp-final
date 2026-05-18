"""AI chat end-to-end."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_chat_interface_renders(page: Page, live_server):
    page.goto(f"{live_server.url}/ai-chat/")
    assert "/ai-chat" in page.url
    assert "/login" not in page.url
    expect(page.locator("body")).to_be_visible()
    expect(page.locator("#chatForm")).to_be_visible()
    expect(page.locator("#messageInput")).to_be_visible()


@pytest.mark.e2e
def test_chat_history_page_loads(page: Page, live_server):
    page.goto(f"{live_server.url}/ai-chat/history/")
    assert "/ai-chat/history" in page.url
    assert "/login" not in page.url
    expect(page.locator("body")).to_be_visible()


@pytest.mark.e2e
def test_send_message_handles_unconfigured_ai(page: Page, live_server):
    """Without AI provider env vars, send/ must not 500 — it should surface a
    controlled error (503 AIConfigurationError / AIProviderError) or 400."""
    page.goto(f"{live_server.url}/ai-chat/")
    csrf = page.locator('input[name="csrfmiddlewaretoken"]').first.get_attribute("value")
    assert csrf, "CSRF token should be present on the chat page"

    response = page.request.post(
        f"{live_server.url}/ai-chat/send/",
        data='{"message": "hello from e2e"}',
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
            "Referer": f"{live_server.url}/ai-chat/",
        },
    )
    assert response.status != 500, (
        f"send_message returned 500; expected graceful 200/4xx/503. Body: {response.text()}"
    )
    assert response.status in (200, 400, 401, 403, 503), (
        f"Unexpected status {response.status}. Body: {response.text()}"
    )


@pytest.mark.e2e
def test_clear_conversation_endpoint(page: Page, live_server):
    page.goto(f"{live_server.url}/ai-chat/")
    csrf = page.locator('input[name="csrfmiddlewaretoken"]').first.get_attribute("value")
    assert csrf

    response = page.request.post(
        f"{live_server.url}/ai-chat/clear/",
        headers={
            "X-CSRFToken": csrf,
            "Referer": f"{live_server.url}/ai-chat/",
        },
    )
    assert response.status == 200, f"clear_conversation failed: {response.status} {response.text()}"
    body = response.json()
    assert body.get("success") is True
