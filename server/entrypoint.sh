#!/bin/sh

# Exit on any error
set -e

# Default values
APP_ENV=${APP_ENV:-development}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

echo "Starting application in $APP_ENV environment..."

# Check APP_ENV and run appropriate server
if [ "$APP_ENV" = "production" ]; then
    echo "Running Gunicorn for production..."
    exec gunicorn -k uvicorn.workers.UvicornWorker -c /app/gunicorn_conf.py main:app
else
    echo "Running Uvicorn for development..."
    exec uvicorn main:app --host $HOST --port $PORT --reload
fi

# Execute any additional commands passed to the container
exec "$@"