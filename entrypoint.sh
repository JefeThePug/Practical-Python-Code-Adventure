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
        python setup.py "$DISCORD_ADMIN_USER_ID"
    else
        python update_from_2025.py "$DISCORD_ADMIN_USER_ID"
    fi
else
    echo "No DB setup action (SETUP_TYPE=$SETUP_TYPE)"
fi

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:${FLASK_PORT} app.run:app
