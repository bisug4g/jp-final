#!/usr/bin/env sh
set -e

# Run DB migrations before starting the server. Blocks boot so we never serve
# traffic against an unmigrated schema.
echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

# Optionally ensure an initial user exists (no-op unless env vars are set).
if [ -n "${INITIAL_USERNAME:-}" ] && [ -n "${INITIAL_PASSWORD:-}" ]; then
  echo "[entrypoint] Ensuring initial user..."
  python manage.py create_initial_user || true
fi

# Seed welcome content on first boot (idempotent — skips if content already exists).
echo "[entrypoint] Seeding initial content (idempotent)..."
python manage.py seed_content 2>/dev/null || true

PORT="${PORT:-8001}"
echo "[entrypoint] Starting gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn jaytipargal.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
