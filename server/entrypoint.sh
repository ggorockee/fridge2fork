#!/bin/bash
set -e

echo "🚀 Starting entrypoint script..."
echo "Environment: ${ENVIRONMENT:-development}"

# Wait for PostgreSQL to be ready
if [ -n "$POSTGRES_SERVER" ]; then
    echo "⏳ Waiting for PostgreSQL at $POSTGRES_SERVER:${POSTGRES_PORT:-5432}..."

    max_attempts=30
    attempt=0

    while ! pg_isready -h "$POSTGRES_SERVER" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ PostgreSQL is not available after $max_attempts attempts"
            exit 1
        fi
        echo "Attempt $attempt/$max_attempts: PostgreSQL is unavailable - sleeping"
        sleep 2
    done

    echo "✅ PostgreSQL is ready!"
fi

# Run migrations (only in init container for k8s, but safe to run here too)
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "📦 Running database migrations..."
    cd /app/app

    # Create migrations if AUTO_MIGRATE is true
    if [ "${AUTO_MIGRATE:-false}" = "true" ]; then
        echo "🔧 Creating migrations..."
        uv run python manage.py makemigrations --noinput || {
            echo "⚠️  makemigrations failed, but continuing..."
        }
    fi

    # Apply migrations
    echo "🔧 Applying migrations..."
    uv run python manage.py migrate --noinput || {
        echo "❌ Migration failed!"
        exit 1
    }

    echo "✅ Migrations completed successfully"
    cd /app
fi

# Collect static files for production
if [ "${ENVIRONMENT}" = "production" ] && [ "${COLLECT_STATIC:-true}" = "true" ]; then
    echo "📦 Collecting static files..."
    cd /app/app
    uv run python manage.py collectstatic --noinput || {
        echo "⚠️  collectstatic failed, but continuing..."
    }
    cd /app
    echo "✅ Static files collected"
fi

# Create superuser for development (optional)
if [ "${ENVIRONMENT}" = "development" ] && [ "${CREATE_SUPERUSER:-false}" = "true" ]; then
    echo "👤 Creating superuser..."
    cd /app/app
    uv run python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME:-admin}').exists():
    User.objects.create_superuser(
        username='${DJANGO_SUPERUSER_USERNAME:-admin}',
        email='${DJANGO_SUPERUSER_EMAIL:-admin@example.com}',
        password='${DJANGO_SUPERUSER_PASSWORD:-admin}'
    )
    print('✅ Superuser created successfully')
else:
    print('ℹ️  Superuser already exists')
EOF
    cd /app
fi

echo "🎉 Entrypoint script completed!"
echo "🚀 Starting application..."

# Execute the main command
exec "$@"
