#!/bin/bash

# Exit on any error
set -e

# Default values with K8s environment support
APP_ENV=${APP_ENV:-${BUILD_MODE:-production}}
ENVIRONMENT=${ENVIRONMENT:-${BUILD_MODE:-production}}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
TIMEOUT=${TIMEOUT:-120}
KEEPALIVE=${KEEPALIVE:-5}
MAX_REQUESTS=${MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}

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

    # Run Alembic migrations automatically
    log "🔄 Running Alembic database migrations..."

    # Show current migration status
    log "📊 Current migration status:"
    alembic current || warn "Could not determine current migration version"

    # Show pending migrations
    log "📋 Checking for pending migrations..."
    PENDING=$(alembic heads | head -1)
    log "Target migration: $PENDING"

    # Run migrations with verbose output
    log "⬆️  Applying migrations..."
    if alembic upgrade head --verbose; then
        success "✅ Database migrations completed successfully"

        # Show final migration status
        log "📊 Final migration status:"
        alembic current

        # List all applied migrations
        log "📜 Migration history:"
        alembic history | head -20
    else
        error "❌ Database migration failed. Exiting..."
        error "Please check the migration files in migrations/versions/"
        exit 1
    fi
else
    warn "DATABASE_URL not set. Skipping database connection check and migrations."
fi

# Check if any arguments are passed to the container
if [ $# -gt 0 ]; then
    log "Executing custom command: $*"
    exec "$@"
fi

# Check APP_ENV and run appropriate server
if [ "$APP_ENV" = "prod" ] || [ "$APP_ENV" = "production" ]; then
    log "🔥 Running Gunicorn for production environment..."
    log "Workers: $WORKERS"
    log "Timeout: $TIMEOUT seconds"
    log "Keep-alive: $KEEPALIVE seconds"
    log "Max requests: $MAX_REQUESTS (jitter: $MAX_REQUESTS_JITTER)"

    exec gunicorn main:app \
        -c gunicorn.conf.py \
        --bind $HOST:$PORT \
        --workers $WORKERS \
        --timeout $TIMEOUT \
        --keepalive $KEEPALIVE \
        --max-requests $MAX_REQUESTS \
        --max-requests-jitter $MAX_REQUESTS_JITTER
elif [ "$APP_ENV" = "dev" ] || [ "$APP_ENV" = "development" ] || [ "$APP_ENV" = "develop" ]; then
    log "🔧 Running Uvicorn for development environment..."
    exec uvicorn main:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level debug
else
    error "Invalid APP_ENV: $APP_ENV. Must be 'prod', 'production', 'dev', 'development', or 'develop'"
    exit 1
fi