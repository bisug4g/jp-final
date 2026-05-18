"""Accessibility audits via axe-core (axe-playwright-python).

Strategy
--------
Inject axe-core into each page and collect violations. Because the app has
pre-existing a11y issues we can't fix in this change, we maintain a per-page
baseline of allowed rule ids in ``_a11y_baseline.json``. The test asserts:

* No **new** serious/critical rule ids appear on a page (no regressions).
* Moderate/minor impacts are ignored (too noisy for a Django/Bootstrap UI).

On first run (no baseline file) the current violations are written to the
baseline file and the test passes. Fixing a violation? Just delete its entry
from the baseline.

Falls back to injecting axe-core from the jsDelivr CDN if
``axe-playwright-python`` is unavailable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page

try:  # pragma: no cover - exercised by install, not by logic
    from axe_playwright_python.sync_playwright import Axe  # type: ignore

    _AXE = Axe()
    _USE_LIB = True
except Exception:  # noqa: BLE001 - any import failure triggers fallback
    _AXE = None
    _USE_LIB = False


AXE_CDN = "https://cdn.jsdelivr.net/npm/axe-core@4.10.0/axe.min.js"
BASELINE_PATH = Path(__file__).parent / "_a11y_baseline.json"
TRACKED_IMPACTS = {"serious", "critical"}


def _run_axe(page: Page) -> list[dict[str, Any]]:
    """Run axe-core against the current page and return the violations list."""
    if _USE_LIB:
        result = _AXE.run(page)
        raw = getattr(result, "response", None) or {}
        return list(raw.get("violations", []))

    page.add_script_tag(url=AXE_CDN)
    raw = page.evaluate("async () => await axe.run()")
    return list(raw.get("violations", []))


def _load_baseline() -> dict[str, list[str]]:
    if BASELINE_PATH.exists():
        try:
            return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_baseline(baseline: dict[str, list[str]]) -> None:
    BASELINE_PATH.write_text(
        json.dumps(baseline, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _summarise(violations: list[dict[str, Any]]) -> list[tuple[str, str, int]]:
    return [
        (v.get("id", "?"), v.get("impact") or "unknown", len(v.get("nodes", [])))
        for v in violations
    ]


def _audit(page: Page, label: str) -> None:
    """Audit the current page against the baseline; fail on regressions."""
    page.wait_for_load_state("domcontentloaded")
    violations = _run_axe(page)

    tracked = [v for v in violations if (v.get("impact") in TRACKED_IMPACTS)]
    current_ids = sorted({v.get("id", "?") for v in tracked})

    if tracked:
        print(f"[a11y][{label}] tracked (serious/critical) violations:")
        for rule, impact, nodes in _summarise(tracked):
            print(f"  - {rule} ({impact}) x{nodes}")

    baseline = _load_baseline()

    if label not in baseline:
        baseline[label] = current_ids
        _save_baseline(baseline)
        print(
            f"[a11y][{label}] seeded baseline with "
            f"{len(current_ids)} rule(s): {current_ids}"
        )
        return

    allowed = set(baseline[label])
    regressions = sorted(set(current_ids) - allowed)
    assert not regressions, (
        f"{label}: new a11y regressions vs baseline: {regressions}. "
        f"Fix them or, if intentional, update {BASELINE_PATH.name}."
    )


# -- Login (anonymous) -------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.a11y
def test_a11y_login(anon_page: Page, live_server):
    anon_page.goto(f"{live_server.url}/")
    _audit(anon_page, "login")


# -- Authenticated pages ------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.a11y
def test_a11y_dashboard(page: Page, live_server):
    page.goto(f"{live_server.url}/")
    _audit(page, "dashboard")


@pytest.mark.e2e
@pytest.mark.a11y
def test_a11y_notes_list(page: Page, live_server):
    page.goto(f"{live_server.url}/notes/")
    _audit(page, "notes")


@pytest.mark.e2e
@pytest.mark.a11y
def test_a11y_diary_overview(page: Page, live_server):
    page.goto(f"{live_server.url}/diary/")
    _audit(page, "diary")


@pytest.mark.e2e
@pytest.mark.a11y
def test_a11y_goals_list(page: Page, live_server):
    page.goto(f"{live_server.url}/goals/")
    _audit(page, "goals")


@pytest.mark.e2e
@pytest.mark.a11y
def test_a11y_astro_dashboard(page: Page, live_server):
    page.goto(f"{live_server.url}/astro/")
    _audit(page, "astro")


@pytest.mark.e2e
@pytest.mark.a11y
def test_a11y_profile(page: Page, live_server):
    page.goto(f"{live_server.url}/profile/")
    _audit(page, "profile")
