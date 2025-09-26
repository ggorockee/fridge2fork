#!/bin/bash

# Exit on any error
set -e

# Default values
APP_ENV=${APP_ENV:-production}
ENVIRONMENT=${ENVIRONMENT:-production}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
TIMEOUT=${TIMEOUT:-120}
KEEPALIVE=${KEEPALIVE:-5}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Check if running as root (should not be in production)
if [ "$(id -u)" = "0" ]; then
    warn "Running as root user. This is not recommended for production."
fi

# Validate environment
log "🚀 Starting Fridge2Fork API"
log "Environment: $ENVIRONMENT"
log "App Environment: $APP_ENV"
log "Host: $HOST"
log "Port: $PORT"

# Wait for database (if DATABASE_URL is set)
if [ -n "$DATABASE_URL" ]; then
    log "Checking database connection..."
    python -c "
import asyncio
import asyncpg
import os
import sys
from urllib.parse import urlparse

async def check_db():
    try:
        db_url = os.getenv('DATABASE_URL')
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        # Parse URL to get connection params
        parsed = urlparse(db_url)
        
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/')
        )
        await conn.close()
        print('Database connection successful')
    except Exception as e:
        print(f'Database connection failed: {e}')
        sys.exit(1)

asyncio.run(check_db())
" || {
        error "Database connection failed. Exiting..."
        exit 1
    }
    success "Database connection successful"
fi

# Run database migrations if in production
if [ "$APP_ENV" = "production" ] && [ -f "alembic.ini" ]; then
    log "Running database migrations..."
    python -m alembic upgrade head || {
        error "Database migration failed. Exiting..."
        exit 1
    }
    success "Database migrations completed"
fi

# Check if any arguments are passed to the container
if [ $# -gt 0 ]; then
    log "Executing custom command: $*"
    exec "$@"
fi

# Check APP_ENV and run appropriate server
if [ "$APP_ENV" = "production" ]; then
    log "🔥 Running Gunicorn for production..."
    log "Workers: $WORKERS"
    log "Timeout: $TIMEOUT seconds"
    log "Keep-alive: $KEEPALIVE seconds"
    
    exec gunicorn main:app \
        -k uvicorn.workers.UvicornWorker \
        --bind $HOST:$PORT \
        --workers $WORKERS \
        --timeout $TIMEOUT \
        --keepalive $KEEPALIVE \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload \
        --access-logfile - \
        --error-logfile - \
        --log-level info
elif [ "$APP_ENV" = "development" ]; then
    log "🔧 Running Uvicorn for development..."
    exec uvicorn main:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level debug
else
    error "Invalid APP_ENV: $APP_ENV. Must be 'production' or 'development'"
    exit 1
fi