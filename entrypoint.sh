#!/bin/bash
set -e

echo "Starting container..."

# --- Gunicorn Phase ---
WORKERS=${GUNICORN_WORKERS:-2}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
FLASK_PORT=${FLASK_PORT:-5000}

echo "Starting gunicorn (workers=$WORKERS, timeout=$TIMEOUT, port=$FLASK_PORT)..."

exec uv run gunicorn \
    --bind "0.0.0.0:${FLASK_PORT}" \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app.run:app
