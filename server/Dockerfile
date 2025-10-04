# syntax=docker/dockerfile:1

# Multi-stage build for Python 3.12 with uv
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*



RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy uv from .local/bin to /usr/local/bin for global access
RUN echo "=== UV Installation Verification ===" && \
    echo "Searching for uv in /root/.local..." && \
    find /root/.local -name uv -type f 2>/dev/null && \
    echo "Copying uv to /usr/local/bin..." && \
    cp /root/.local/bin/uv /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv && \
    echo "UV copied to /usr/local/bin/uv"

# Final verification
RUN echo "=== Final UV Check ===" && \
    which uv && echo "UV is available at: $(which uv)" && \
    uv --version




# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Development stage
FROM base AS dev

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    UV_NO_SYNC=1 \
    DJANGO_SETTINGS_MODULE=settings.settings \
    ENVIRONMENT=development

# Create UV cache directory with write permissions
RUN mkdir -p /tmp/.uv-cache && chmod -R 777 /tmp/.uv-cache

# Install dependencies with uv (frozen mode - no lock file updates)
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . .

# Set proper permissions for /app directory
RUN chmod -R 755 /app && \
    mkdir -p /app/logs /app/staticfiles /app/mediafiles && \
    chmod -R 777 /app/logs /app/staticfiles /app/mediafiles

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for development (use --frozen to prevent lock file updates)
CMD ["/usr/local/bin/uv", "run", "--frozen", "python", "app/manage.py", "runserver", "0.0.0.0:8000"]


# Production stage
FROM base AS prod

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    UV_NO_SYNC=1 \
    DJANGO_SETTINGS_MODULE=settings.settings \
    ENVIRONMENT=production

# Create UV cache directory with write permissions
RUN mkdir -p /tmp/.uv-cache && chmod -R 777 /tmp/.uv-cache

# Install dependencies with uv (production only, no dev dependencies, frozen mode)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Set proper permissions for /app directory
RUN chmod -R 755 /app && \
    mkdir -p /app/logs /app/staticfiles /app/mediafiles && \
    chmod -R 777 /app/logs /app/staticfiles /app/mediafiles

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Collect static files
RUN uv run --frozen python app/manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for production (gunicorn with --frozen flag)
CMD ["/usr/local/bin/uv", "run", "--frozen", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--chdir", "app", "settings.wsgi:application"]
