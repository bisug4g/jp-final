# Jayti Personal Companion — Gemini CLI Context

This is **JAYTI**, a personal life companion web app built as a birthday gift.
Use this file as your primary reference for every task in this codebase.

---

## What this project is

A Django 4.2 web application deployed on **Firebase Hosting + Google Cloud Run + Cloud SQL**.
It is a personal app for one user (Jayati) — not a multi-tenant SaaS.

Built with love by Vivek. Every decision should feel personal, warm, and thoughtful.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2, Python 3.11, ASGI (Uvicorn + Gunicorn) |
| Database | PostgreSQL (Cloud SQL in prod, SQLite in dev) |
| Frontend | Django Templates, Bootstrap 5, Chart.js, Vanilla JS |
| AI | Google Gemini (primary), OpenAI-compatible Emergent (secondary) |
| Static files | WhiteNoise (served from Cloud Run) |
| Hosting | Firebase Hosting → Cloud Run (asia-south1) |
| Android | Native WebView APK in `android/` (Kotlin, API 26+) |
| Auth | Django session auth, single user |

---

## Project Structure

```
jp-final/
├── core/           # Auth, dashboard, activity tracker, notifications, middleware
├── notes/          # Notes with folders, tags, pin, search, PDF export
├── diary/          # Daily journal, mood tracking, streaks
├── goals/          # Goals + AI-generated tasks, Kanban board
├── astro/          # Vedic astrology (Swiss Ephemeris), birth chart, Dasha
├── ai_chat/        # AI companion chat (Gemini / Emergent)
├── tangred/        # Wardrobe AI with photo sessions and Tan Studio styleboards
├── android/        # Native Android APK (WebView wrapper + E2E tests)
├── templates/      # Django HTML templates (per-app subdirectories)
├── static/         # CSS, JS, PWA manifest, service worker, icons
├── jaytipargal/    # Django project settings, URLs, ASGI
├── firebase.json   # Firebase Hosting config (rewrites to Cloud Run)
├── cloudbuild.yaml # Google Cloud Build CI/CD pipeline
├── Dockerfile      # Production container (Python 3.11-slim)
├── entrypoint.sh   # Container entrypoint: migrate → seed → gunicorn
├── LAUNCH_FIREBASE.md  # Complete Firebase deployment guide
└── GEMINI.md       # ← you are here
```

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `jaytipargal/settings.py` | All Django settings; reads from env vars |
| `core/models.py` | UserProfile, DailyActivity, Notifications, DailyThought |
| `core/views.py` | Dashboard, login, profile, session management |
| `core/services/ai_runtime.py` | AI provider abstraction (Gemini / Emergent / GitHub Models) |
| `core/services/daily_briefing.py` | AI morning briefing generator |
| `astro/views.py` | Vedic astrology — largest file (37 KB), touch carefully |
| `tangred/services/agent.py` | Wardrobe AI agent (OpenRouter + Stitch MCP) |
| `android/app/src/main/java/com/jayti/companion/MainActivity.kt` | Android WebView host |

---

## Development Conventions

### Python / Django
- **Formatter:** not enforced (legacy codebase); keep existing style
- **Linter:** `ruff check .` — only E9, F, B rules (see `pyproject.toml`)
- **Tests:** `pytest tests -q --ignore=tests/e2e` — must stay green
- **Migrations:** always run `python manage.py makemigrations` after model changes
- **No direct SQL** — use Django ORM throughout
- **Error handling:** broad `except` blocks are intentional in many places (personal app; resilience > strictness)

### Templates
- Base template: `templates/base.html` — includes dark mode, PWA scripts, Firebase init
- All templates extend `base.html` via `{% extends "base.html" %}`
- Pink/coral theme (`#E91E8C`, `#FF69B4`) — keep the warmth in UI additions

### AI providers (in priority order)
1. `EMERGENT_API_KEY` → OpenAI-compatible, primary (claude-opus-4-6)
2. `GEMINI_API_KEY` → Google Gemini (gemini-1.5-pro)
3. `GITHUB_MODELS_TOKEN` → GitHub Models (gpt-4.1-mini)
4. Vertex AI → via Firebase credentials

### Static files
- Source: `static/` directory
- Collected to: `staticfiles/` via `python manage.py collectstatic`
- Served by: WhiteNoise in production

---

## Environment Variables

Never hardcode secrets. All sensitive config is in env vars (Secret Manager in prod).
See `backend/.env.firebase.example` for the full list.

Key ones:
```
SECRET_KEY          Django secret key (required in prod)
DATABASE_URL        PostgreSQL connection string
GEMINI_API_KEY      Google Gemini API key
EMERGENT_API_KEY    Emergent/OpenAI-compatible API key
VAPID_PUBLIC_KEY    Web push notifications
FIREBASE_PROJECT_ID Firebase project (jpfinal-bisu-2026)
```

---

## Running Locally

```bash
# Install
pip install -r requirements.txt

# Set up env
cp backend/.env.firebase.example backend/.env
# Edit backend/.env with your keys

# Database
python manage.py migrate
python manage.py create_initial_user --username jayati --password yourpass
python manage.py seed_content
python manage.py loaddata core/fixtures/initial_data.json

# Run
python manage.py runserver
```

---

## Testing

```bash
# Unit + smoke tests (fast, no browser)
pytest tests -q --ignore=tests/e2e

# Django deploy check (mimics production)
DEBUG=False SECRET_KEY=test-key ALLOWED_HOSTS=example.com python manage.py check --deploy

# Lint
ruff check .

# Android E2E (requires connected device or emulator)
cd android && ./gradlew connectedAndroidTest
```

---

## Deployment

Full guide: **`LAUNCH_FIREBASE.md`**

Quick deploy:
```bash
git push origin main   # triggers Cloud Build automatically
```

Manual one-shot:
```bash
gcloud run deploy jayti \
  --image=asia-south1-docker.pkg.dev/jpfinal-bisu-2026/jayti/app:latest \
  --region=asia-south1 --platform=managed
firebase deploy --only hosting
```

---

## Android APK

```bash
cd android
./gradlew assembleDebug          # builds jayti-v1.0-debug.apk
./gradlew assembleRelease        # builds release APK (needs keystore)
./gradlew connectedAndroidTest   # runs E2E suite on device
```

Install on phone: `adb install android/app/build/outputs/apk/debug/app-debug.apk`

---

## What Gemini CLI can help with in this project

- **Add a new Django app:** `gemini "Add a [habits/reading/budget] tracking module with model, views, urls, and template"`
- **Write a migration:** `gemini "Write a Django migration to add [field] to [model]"`
- **Debug:** `gemini "Here is the traceback: [paste] — what's wrong and how do I fix it?"`
- **Write tests:** `gemini "Write pytest tests for the diary PDF export view"`
- **Refactor:** `gemini "Refactor astro/views.py to extract the Dasha calculation into a service"`
- **Android:** `gemini "Add a biometric lock to the Android app"`
- **Deploy:** `gemini "What Cloud Build step do I need to add to run seed_content only on first deploy?"`

---

## Important Notes for AI Assistance

1. **This is a personal app** — one user, one database. Don't suggest multi-tenant patterns.
2. **Keep it warm.** The UI uses soft pinks and encouraging language. Match that energy.
3. **Preserve existing migrations** — never delete or squash migration files.
4. **The astro module uses pyswisseph** — Swiss Ephemeris, not a REST API. Don't suggest replacing it.
5. **Tangred is experimental** — the wardrobe AI feature, handle with care.
6. **Firebase project ID is `jpfinal-bisu-2026`** — use this when generating gcloud commands.
7. **Region is `asia-south1` (Mumbai)** — all Cloud Run / Cloud SQL / Artifact Registry resources live here.
