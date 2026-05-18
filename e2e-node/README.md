# Local Playwright harness (Node)

Optional Node-based Playwright harness for developers who want `playwright
codegen` or the `show-trace` UI, plus **visual regression tests**. The smoke
and visual suites here are not the authoritative Python CI suite (see
`tests/e2e/README.md`) — treat this as a local/opt-in tool.

## Usage

```bash
# From the repo root, start Django:
python manage.py runserver 127.0.0.1:8000

# In another terminal:
cd e2e-node
npm install
npm run install-browsers
E2E_BASE_URL=http://127.0.0.1:8000 npm test
```

Both `E2E_BASE_URL` and `BASE_URL` are honoured (defaults to
`http://127.0.0.1:8000`).

## Recording new flows

```bash
npm run codegen -- http://127.0.0.1:8000
```

Save the generated spec to `tests/` and port the assertions into the Python
suite if you want them to run in CI.

## Visual regression tests

`tests/visual.spec.ts` captures full-page screenshots for the critical
screens and compares against committed baselines under
`tests/__screenshots__/visual.spec.ts/`. Comparison uses Playwright's native
`toHaveScreenshot()` with `maxDiffPixelRatio: 0.02`, `threshold: 0.2`, and
`animations: 'disabled'`.

### Requirements

- A running Django server reachable at `BASE_URL`.
- A pre-seeded user whose credentials are exported as environment variables:
  - `E2E_USERNAME`
  - `E2E_PASSWORD`

### Running

```powershell
# From e2e-node/
$env:BASE_URL       = "http://127.0.0.1:8000"
$env:E2E_USERNAME   = "visual-tester"
$env:E2E_PASSWORD   = "visual-pass-123"

npm run test:visual
```

### Pages covered

| Test                           | URL        | Auth  |
| ------------------------------ | ---------- | ----- |
| `login screen (anonymous)`     | `/`        | no    |
| `dashboard (/)`                | `/`        | yes   |
| `notes`                        | `/notes/`  | yes   |
| `diary`                        | `/diary/`  | yes   |
| `goals`                        | `/goals/`  | yes   |
| `astro`                        | `/astro/`  | yes   |

Dynamic regions (timestamps, greeting, daily briefing, birthday banner,
`<time>` elements, `[data-testid="current-time"]`, `.timestamp`,
`.greeting`) are masked out. Anti-aliasing noise is absorbed by the
`maxDiffPixelRatio` of 2 %.

### Updating baselines intentionally

When a UI change is expected, regenerate and commit the new snapshots:

```powershell
npm run test:visual -- --update-snapshots
git add tests/__screenshots__
git commit -m "visual: update baselines for <change>"
```

### OS sensitivity (important!)

Playwright's pixel comparisons are OS- and browser-version-dependent —
a baseline captured on Windows will *not* match Linux or macOS renderings.

This repo's CI (GitHub Actions, Ubuntu) uses Linux, and **the baselines
committed under `tests/__screenshots__/visual.spec.ts/` are Linux
(Ubuntu/jammy) renderings generated inside the official
`mcr.microsoft.com/playwright:v1.59.1-jammy` Docker image.** They match CI
out of the box — no regeneration is needed unless the UI actually changed.

Running `npm run test:visual` directly on Windows will diff against those
Linux baselines and will fail on sub-pixel font/AA rendering. For local
visual runs on Windows, either:

- Run the suite inside the same Linux Docker image (recipe below), or
- Expect local diffs and rely on CI / Docker for the authoritative result.

#### Regenerating the Linux baselines from Windows (only when intentional)

```powershell
# 1. From the repo root, start Django so it binds on all interfaces:
$env:DEBUG="True"; $env:SECRET_KEY="dev"; $env:ALLOWED_HOSTS="*"
python manage.py runserver 0.0.0.0:8765 --noreload

# 2. In another terminal, run the Playwright Linux container against the
#    host's Django. host.docker.internal maps to the Windows host under
#    Docker Desktop; --add-host is needed for non-Desktop Docker.
docker run --rm `
  -v "${PWD}:/work" -w /work/e2e-node `
  --add-host=host.docker.internal:host-gateway `
  -e BASE_URL=http://host.docker.internal:8765 `
  -e E2E_USERNAME=visual-tester `
  -e E2E_PASSWORD=visual-pass-123 `
  mcr.microsoft.com/playwright:v1.59.1-jammy `
  sh -c "npm ci --no-audit --no-fund --silent && npx playwright test visual.spec.ts --update-snapshots"

# 3. Verify the new baselines are a clean match:
docker run --rm `
  -v "${PWD}:/work" -w /work/e2e-node `
  --add-host=host.docker.internal:host-gateway `
  -e BASE_URL=http://host.docker.internal:8765 `
  -e E2E_USERNAME=visual-tester `
  -e E2E_PASSWORD=visual-pass-123 `
  mcr.microsoft.com/playwright:v1.59.1-jammy `
  sh -c "npx playwright test visual.spec.ts"

# 4. Commit the updated PNGs under tests/__screenshots__/.
```

Keep the image tag aligned with the `@playwright/test` version pinned in
`package.json` (bump both together). Never commit Windows-rendered PNGs —
they will break CI.

### Baselines are committed

`e2e-node/.gitignore` explicitly keeps `tests/__screenshots__/` so baselines
travel with the repo. Do not remove that allowlist without also updating
this README.

## Performance budgets (`tests/perf.spec.ts`)

`perf.spec.ts` asserts page-load budgets using the browser's Navigation
Timing API (`performance.getEntriesByType('navigation')[0]`) — no Lighthouse
or extra infra required. Budgets are enforced for both DOMContentLoaded
(DCL) and the Load event; the measured values are attached as Playwright
annotations (`type: 'perf'`) and logged to stdout for CI visibility.

Current budgets (intentionally generous; tighten as the app is optimised):

| Page                 | DCL      | Load     |
| -------------------- | -------- | -------- |
| Login `/` (anon)     | < 2500ms | < 3500ms |
| Dashboard `/` (auth) | < 2500ms | < 5000ms |
| Notes `/notes/`      | < 2000ms | < 4000ms |
| Diary `/diary/`      | < 2000ms | < 4000ms |
| Goals `/goals/`      | < 2000ms | < 4000ms |
| Astro `/astro/`      | < 3000ms | < 6000ms |

The suite runs serially (`test.describe.configure({ mode: 'serial' })`) to
minimise system noise, and calls `test.slow()` for CI headroom. A warmup
hit to `/health` runs before the first measurement to amortise Django
dev-server template compilation.

### How to run

```powershell
# From the repo root, start Django (DEBUG=True to skip SSL redirect):
$env:DEBUG="True"; $env:SECRET_KEY="dev"; $env:ALLOWED_HOSTS="127.0.0.1,localhost"
python manage.py runserver 127.0.0.1:8000

# Seed a test user (once):
python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); u,_=U.objects.get_or_create(username='perf-tester'); u.set_password('perf-pass-123'); u.save()"

# In another terminal:
cd e2e-node
$env:BASE_URL="http://127.0.0.1:8000"
$env:E2E_USERNAME="perf-tester"
$env:E2E_PASSWORD="perf-pass-123"
npm run test:perf
```

If a page consistently exceeds its budget on a healthy machine, either
optimise the page or raise the budget in `perf.spec.ts` with a comment
explaining why.
