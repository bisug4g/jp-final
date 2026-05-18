# JAYTI - Product Requirements Document

## Original Problem Statement
Build a personal, feature-rich website called "JAYTI" as a birthday gift with:
- Notes, Diary, Goals, Vedic Astrology, and AI Companion features
- Production-ready deployment on Emergent platform
- Custom domain: jaytibirthday.in

---

## Architecture
```
Frontend (Port 3000) - Node.js Proxy (server.js → proxies to Django on 8001)
    ↓
Backend (Port 8001) - Django ASGI via uvicorn (server.py → jaytipargal.asgi:application)
    ↓
Database - Supabase PostgreSQL (Production) / SQLite (local fallback)
```

## Tech Stack
- Django 4.2, Python 3.11
- Gunicorn + Uvicorn ASGI workers
- Supabase PostgreSQL (ap-south-1)
- Google Gemini 1.5 Pro (lazy-loaded)
- WhiteNoise for static files

---

## Features Implemented
- Login/Auth (single user: jayati)
- Dashboard with activity tracker
- Notes (with folders, pinning, search)
- Diary (with mood tracking, multi-modal input)
- Goals + Tasks (career framework)
- AI Chat (Gemini 1.5 Pro)
- Vedic Astrology (Swiss Ephemeris)
- PWA support (service worker, installable)
- Push notifications (VAPID - configurable)
- Birthday countdown + confetti

---

## What's Been Implemented (Changelog)

### Apr 10, 2026
- Removed hardcoded DomainWatch tracking script from base.html
- Fixed VAPID placeholder — push notifications disabled gracefully if VAPID_PUBLIC_KEY not set
- Cleaned up .gitignore (removed 150+ duplicate entries, removed backend/.env blocking)
- VAPID key now injected dynamically via Django context processor
- Supabase restored and reconnected after free-tier pause
- Smart merge: preserved real Supabase data (4 diary entries, 24 AI messages, Travel note)
- Imported missing SQLite data (goals, tasks, daily thoughts) into Supabase
- Production login credentials were rotated outside the repository.

### Feb 10, 2026
- Complete UI/UX Overhaul — Pink/coral theme, square cards, enterprise grid
- Activity Tracker feature with heatmap calendar
- Deployment health check fixes (/health endpoint)

### Feb 9, 2026
- PostgreSQL migration from SQLite to Supabase
- All apps (Notes, Diary, Goals, Astro, AI Chat) migrated

---

## Deployment Configuration

### Emergent Platform
- Supervisor: `uvicorn server:app` from `/app/backend` (by design — server.py bridges to Django)
- Health check: `GET /health/` → responds in ~0.1s (exempt from CSRF)
- Static files: WhiteNoise (collected at build time)

### Required Secrets (Emergent Deployment Dashboard)
Set these in the Emergent deployment secrets panel:
```
DATABASE_URL=postgresql://<user>:<password>@<host>:6543/<database>
EMERGENT_API_KEY=<set-in-secret-store>
GEMINI_API_KEY=<set-in-secret-store>
SECRET_KEY=<generate-a-unique-secret>
DJANGO_SETTINGS_MODULE=jaytipargal.settings
DEBUG=False
TIME_ZONE=Asia/Kolkata
EMERGENT_MODEL=claude-opus-4-6
GEMINI_MODEL=gemini-1.5-pro
BIRTH_DATE_DAY=6
BIRTH_DATE_MONTH=2
```

---

## Test Credentials
- Production credentials are intentionally excluded from the repository.
- Use the secret store or deployment environment variables when creating or rotating access.

## Database
- Provider: Supabase (Free Tier — pauses after 1 week inactivity)
- Project ID: cnxpguagruczejugkmkf
- Region: ap-south-1 (Mumbai)

## Prioritized Backlog

### P0 (Immediate)
- Verify production deployment succeeds on Emergent

### P1
- Custom domain setup (jaytibirthday.in)
- Supabase keep-alive to prevent free-tier pausing

### P2 (Future)
- Email/push notifications via SendGrid or Twilio
- VAPID keys setup for push notifications
- Upgrade Supabase to Pro tier
