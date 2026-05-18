FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install minimal system dependencies (build tools + libs for psycopg2/pyswisseph)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY requirements.txt /app/requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Collect static files at build time. DJANGO_COLLECTSTATIC=1 lets settings.py
# accept a placeholder SECRET_KEY for this non-runtime step only.
RUN DJANGO_COLLECTSTATIC=1 DEBUG=False python manage.py collectstatic --noinput

# Make entrypoint executable and create a non-root user
RUN chmod +x /app/entrypoint.sh \
    && groupadd --system --gid 1001 app \
    && useradd  --system --uid 1001 --gid app --home /app --shell /usr/sbin/nologin app \
    && chown -R app:app /app

USER app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8001}/health" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]

