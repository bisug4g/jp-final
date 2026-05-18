# 💝 JAYTI — Personal Life Companion

A beautiful, feature-rich personal companion web app built with Django.

![Django](https://img.shields.io/badge/Django-4.2-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Railway](https://img.shields.io/badge/Deployed-Railway-0B0D0E)
![CI](https://github.com/flywithvvk/jp/actions/workflows/ci.yml/badge.svg)

## ✨ Features

| Module | Highlights |
|--------|-----------|
| 📝 **Notes** | Folders, tags, pin, search, PDF export |
| 📔 **Diary** | Daily journal, mood tracking, streaks, PDF export |
| 🎯 **Goals** | AI-powered planning, Kanban tasks, progress charts |
| 🔮 **Astrology** | Birth chart (Kundli), 12 houses, Dasha periods, daily guidance |
| 🤖 **AI Chat** | Personal AI mentor (OpenAI-compatible / Gemini / Vertex AI) |
| 👔 **Tangred** | Agentic wardrobe AI with private photo sessions and Tan Studio styleboards |
| 📍 **Location** | Real-time GPS tracking with interactive map |
| 🔔 **Notifications** | Firebase push notifications + diary reminders |
| 🎂 **Birthday** | Countdown widget, confetti celebration |
| 🌙 **Dark Mode** | System-aware toggle |
| 📱 **PWA** | Installable, offline-capable |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (production) or SQLite (development)

### Installation

```bash
git clone https://github.com/flywithvvk/jp.git
cd jp

pip install -r requirements.txt

cp backend/.env.example backend/.env
# Edit backend/.env with your keys

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key (required when `DEBUG=False`) | Yes (prod) |
| `DATABASE_URL` | PostgreSQL connection string | Yes (prod) |
| `DEBUG` | Debug mode (`False` in production) | No |
| `ALLOWED_HOSTS` | Comma-separated host allowlist | No |
| `CSRF_TRUSTED_ORIGIN(S)` | Extra CSRF origins (comma-separated) | No |
| `INITIAL_USERNAME` / `INITIAL_PASSWORD` | Bootstraps the first user on deploy (no-op if unset) | No |
| `LOG_TO_FILE` | Enable file logging (defaults off in prod; Railway fs is ephemeral) | No |
| `EMERGENT_PLATFORM` | Set to `1` to enable Emergent-platform `ALLOWED_HOSTS`/CSRF defaults | No |
| `EMERGENT_API_KEY` | OpenAI-compatible AI provider key | No* |
| `GITHUB_MODELS_TOKEN` | GitHub Models inference token | No* |
| `GEMINI_API_KEY` | Google Gemini API key | No* |
| `VAPID_PUBLIC_KEY` | Web push notification key | No |
| `FIREBASE_PROJECT_ID` | Firebase project identifier | No |

\* At least one AI provider is required for AI chat features.

## 📁 Project Structure

```
jp/
├── core/               # Auth, dashboard, location tracking, middleware
├── notes/              # Notes with folders & tags
├── diary/              # Daily journal & mood tracking
├── goals/              # Goals & task management
├── astro/              # Vedic astrology engine
├── ai_chat/            # AI companion
├── templates/          # Django HTML templates
├── static/             # CSS, JS, icons, PWA manifest
├── backend/            # Server config & requirements
├── firebase-functions/ # Firebase Cloud Functions (proxy)
├── firebase-hosting/   # Firebase Hosting (redirect shell)
├── docs/               # Architecture & deployment guides
└── manage.py
```

## 🛠️ Tech Stack

- **Backend:** Django 4.2, Python 3.11, ASGI (Uvicorn)
- **Database:** PostgreSQL (prod) / SQLite (dev)
- **AI:** OpenAI-compatible, GitHub Models, Gemini, Vertex AI
- **Wardrobe AI:** OpenRouter + Stitch MCP, with durable in-app photo persistence
- **Astrology:** Swiss Ephemeris (pyswisseph)
- **Frontend:** Django Templates, Bootstrap 5, Chart.js, Leaflet.js
- **Deployment:** Railway (ASGI + Gunicorn), WhiteNoise, Firebase Hosting
- **Security:** HSTS, CSRF, XSS protection, SSL redirect, bleach sanitization

## 🚢 Deployment

Deployed on **Railway** with auto-deploy from `main` branch.

The container entrypoint (`entrypoint.sh`) runs DB migrations **before** starting
Gunicorn, so traffic is never served against an unmigrated schema. Railway's
nixpacks build path is equivalent (see `railway.json`). Health probe:
`GET /health` — returns 200 immediately without touching the DB.

```bash
# Local production-style run
docker build -t jayti .
docker run --rm -p 8001:8001 \
  -e SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(64))") \
  -e DEBUG=False \
  -e ALLOWED_HOSTS=localhost \
  jayti
```

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for full setup.

## 🧪 Testing & CI

```bash
# Fast in-process smoke tests
DEBUG=True SECRET_KEY=dev LOG_TO_FILE=0 pytest tests -q --ignore=tests/e2e

# Django deploy check (what CI enforces)
DEBUG=False SECRET_KEY=<long-random> ALLOWED_HOSTS=example.com \
  python manage.py check --deploy --fail-level WARNING

# Lint
ruff check .
```

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR:
lint → tests → Django deploy-check → dependency audit.

### End-to-end (Playwright)

Browser-based E2E tests live in `tests/e2e/` and run against an in-process
Django server via `pytest-django`'s `live_server` fixture.

```bash
pip install -r requirements-dev.txt
playwright install --with-deps chromium
pytest tests/e2e -m e2e -q              # headless
pytest tests/e2e -m e2e --headed        # headed, for debugging
```

CI workflow: `.github/workflows/e2e.yml` (Chromium, traces + screenshots
uploaded as artifacts on failure). See `tests/e2e/README.md` for details. An
optional Node/`@playwright/test` harness for `codegen`/trace UI ships in
`e2e-node/` (not wired into CI).

## Tangred Storage

Tangred session photos are served through authenticated Django endpoints.

- Primary path: Firebase Storage when a valid bucket is configured
- Safe fallback: PostgreSQL-backed binary storage for private in-app persistence
- Optional override: `TANGRED_PRIVATE_MEDIA_BACKEND=database|firebase|local`

This means Tangred wardrobe photos remain available across Railway deploys even when object storage is unavailable.

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Feature Summary](docs/FEATURE_SUMMARY.md)
- [Railway Environment Variables](docs/RAILWAY_ENV_VARS.md)
- [Google Drive Setup](docs/GOOGLE_DRIVE_SETUP.md)

## 📄 License

This project is a personal gift and is not licensed for redistribution.

---

Made with 💕
