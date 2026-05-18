# 🚀 JAYTI — Launch Guide

Everything needed to take the app from code to live at **jaytibirthday.in**.

---

## ✅ Pre-launch Checklist

### 1. Generate a Django SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output — you'll need it in Step 3.

---

### 2. Generate VAPID Keys (push notifications)

```bash
python scripts/generate_vapid_keys.py
```

Copy the three lines printed (`VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_ADMIN_EMAIL`).

---

### 3. Set Railway Environment Variables

In the Railway dashboard → your service → **Variables**, set:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Output from Step 1 |
| `DEBUG` | `False` |
| `TIME_ZONE` | `Asia/Kolkata` |
| `DATABASE_URL` | Auto-set by Railway PostgreSQL plugin |
| `INITIAL_USERNAME` | `jayati` (or your chosen username) |
| `INITIAL_PASSWORD` | A strong password |
| `EMERGENT_API_KEY` | Your Emergent/OpenAI-compatible API key |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `VAPID_PRIVATE_KEY` | Output from Step 2 |
| `VAPID_PUBLIC_KEY` | Output from Step 2 |
| `VAPID_ADMIN_EMAIL` | `admin@jaytibirthday.in` |
| `BIRTH_DATE_DAY` | `6` |
| `BIRTH_DATE_MONTH` | `2` |
| `EMERGENT_MODEL` | `claude-opus-4-6` |
| `GEMINI_MODEL` | `gemini-1.5-pro` |

Optional (Firebase push notifications):
| Variable | Value |
|----------|-------|
| `FIREBASE_PROJECT_ID` | Your Firebase project ID |
| `FIREBASE_API_KEY` | Firebase web API key |
| `FIREBASE_AUTH_DOMAIN` | `<project>.firebaseapp.com` |
| `FIREBASE_STORAGE_BUCKET` | `<project>.appspot.com` |
| `FIREBASE_MESSAGING_SENDER_ID` | Firebase sender ID |
| `FIREBASE_APP_ID` | Firebase app ID |

---

### 4. Add PostgreSQL to Railway

1. In your Railway project, click **+ New** → **Database** → **PostgreSQL**
2. Railway auto-sets `DATABASE_URL` — the app picks it up automatically

---

### 5. Deploy

```bash
git push origin main
```

Railway auto-deploys on push. The `entrypoint.sh` will:
1. Run all DB migrations
2. Create the initial user (from `INITIAL_USERNAME` / `INITIAL_PASSWORD`)
3. Seed welcome content (notes, diary entry, tags)
4. Start Gunicorn

---

### 6. Custom Domain (jaytibirthday.in)

1. In Railway: **Settings** → **Domains** → **Add Custom Domain**
2. Enter `jaytibirthday.in` and `www.jaytibirthday.in`
3. Copy the CNAME records Railway provides
4. In your DNS registrar, add the CNAME records
5. Railway auto-provisions SSL — takes 1–5 minutes

---

### 7. Set Up Supabase Keep-Alive (if using Supabase)

Supabase free tier pauses after 7 days of inactivity. Add a Railway Cron Service:

- **Schedule:** `0 12 */5 * *` (noon every 5 days)  
- **Command:** `python manage.py keepalive_db`

This pings the database and keeps it awake with zero cost.

---

### 8. First Login

1. Go to `https://jaytibirthday.in`
2. Log in with the username/password from `INITIAL_USERNAME` / `INITIAL_PASSWORD`
3. The dashboard will load with welcome notes and sample diary entry already seeded

---

## 🔍 Verify Everything Works

```bash
# Health check
curl https://jaytibirthday.in/health
# → {"status": "healthy", ...}

# API endpoints
curl https://jaytibirthday.in/api/daily-briefing/   # needs login cookie
curl https://jaytibirthday.in/api/goal-progress/
curl https://jaytibirthday.in/api/mood-trends/
curl https://jaytibirthday.in/api/daily-astro/
```

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `SECRET_KEY` error on boot | Set `SECRET_KEY` env var in Railway |
| Static files 404 | Run `python manage.py collectstatic --noinput` (Dockerfile does this at build) |
| AI features not working | Set at least one of `EMERGENT_API_KEY` or `GEMINI_API_KEY` |
| Push notifications not sending | Verify `VAPID_PRIVATE_KEY` and `VAPID_PUBLIC_KEY` are set; requires HTTPS |
| Database paused (Supabase) | Run `python manage.py keepalive_db` or check cron job is active |
| Birthday confetti not showing | Check `BIRTH_DATE_DAY=6` and `BIRTH_DATE_MONTH=2` env vars |

---

## 📋 Post-Launch P1 Tasks

- [ ] Custom domain DNS propagation verified
- [ ] Railway cron for `keepalive_db` set up
- [ ] PWA "Add to Home Screen" tested on mobile
- [ ] Push notification permission granted in browser
- [ ] Vedic birth chart entered in Astro section
- [ ] Consider upgrading Supabase to Pro to avoid sleep

---

*Made with 💕 for Jayti — Happy Birthday!*
