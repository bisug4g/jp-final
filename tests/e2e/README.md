# End-to-end tests (Playwright)

Browser-based E2E suite that drives the real Django app through Chromium. The
suite uses ``pytest-playwright`` together with ``pytest-django``'s
``live_server`` fixture, so everything runs in one process against a fresh test
database — no external infrastructure required.

## Layout

```
tests/e2e/
├── conftest.py          # live_server + authenticated storage_state fixtures
├── test_auth.py         # login, invalid login, logout
├── test_dashboard.py    # dashboard / profile / health
├── test_notes.py        # notes CRUD
├── test_diary.py        # diary write
├── test_goals.py        # goals create
└── test_astro.py        # astrology pages smoke
```

## Running locally

```bash
# 1. Install dev deps (use a venv)
pip install -r requirements-dev.txt
playwright install --with-deps chromium

# 2. Run the full E2E suite (headless)
pytest tests/e2e -m e2e -q

# 3. Headed / slow-mo for debugging
pytest tests/e2e -m e2e --headed --slowmo 250

# 4. Capture a trace for a failing test
pytest tests/e2e -m e2e --tracing=retain-on-failure
# Then open the trace:
playwright show-trace test-results/<trace>.zip
```

## Environment

The tests create their own user (``e2e-tester``) in the per-session test DB. To
point the suite at a non-default user (e.g. against staging), set:

```bash
export E2E_USERNAME=...
export E2E_PASSWORD=...
```

## CI

The ``.github/workflows/e2e.yml`` job runs this suite on every push and PR,
caches the Playwright browser bundle, and uploads ``test-results/`` (traces,
videos, screenshots) as an artifact on failure.
