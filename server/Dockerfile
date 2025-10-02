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

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

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
    DJANGO_SETTINGS_MODULE=settings.settings \
    ENVIRONMENT=development

# Install dependencies with uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for development
CMD ["/root/.local/bin/uv", "run", "python", "app/manage.py", "runserver", "0.0.0.0:8000"]


# Production stage
FROM base AS prod

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    DJANGO_SETTINGS_MODULE=settings.settings \
    ENVIRONMENT=production

# Install dependencies with uv (production only, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Collect static files
RUN uv run python app/manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for production (gunicorn)
CMD ["/root/.local/bin/uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--chdir", "app", "settings.wsgi:application"]
