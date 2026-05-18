web: cd /app && gunicorn jaytipargal.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8001} --workers 2 --timeout 120 --preload
