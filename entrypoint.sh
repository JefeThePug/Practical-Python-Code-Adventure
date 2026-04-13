#!/bin/bash
set -e

echo "Starting container..."

if [ "$SETUP_TYPE" = "setup" ] || [ "$SETUP_TYPE" = "update" ]; then
    if [ -z "$DISCORD_ADMIN_USER_ID" ]; then
        echo "Error: DISCORD_ADMIN_USER_ID is not set!"
        exit 1
    fi

    echo "Running $SETUP_TYPE..."

    if [ "$SETUP_TYPE" = "setup" ]; then
        uv run python setup.py "$DISCORD_ADMIN_USER_ID"
    else
        uv run python update_from_2025.py "$DISCORD_ADMIN_USER_ID"
    fi
else
    echo "No DB setup action (SETUP_TYPE=${SETUP_TYPE:-unset})"
fi

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
