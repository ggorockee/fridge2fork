# Multi-stage build for Fridge2Fork API
# Builder stage
FROM python:3.11-slim-bookworm AS builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel for better dependency handling
RUN pip install --no-cache-dir --upgrade pip wheel

# Copy all requirements files for better caching
COPY requirements.common.txt requirements.prod.txt requirements.dev.txt ./

# Build argument to determine environment-specific dependencies
ARG BUILD_ENV=prod

# Install dependencies based on BUILD_ENV
RUN if [ "$BUILD_ENV" = "dev" ]; then \
        pip install --no-cache-dir -r requirements.dev.txt; \
    else \
        pip install --no-cache-dir -r requirements.prod.txt; \
    fi

# Final stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Create non-root user with home directory
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Add virtual environment to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code (excluding files in .dockerignore)
COPY --chown=appuser:appuser . /app

# Set entrypoint script permissions
RUN chmod +x /app/entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Build arguments for environment configuration
ARG BUILD_MODE=production
ARG BUILD_ENV=prod

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BUILD_MODE=${BUILD_MODE} \
    BUILD_ENV=${BUILD_ENV}

# Expose port
EXPOSE 8000

# Add healthcheck for K8s liveness probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/fridge2fork/v1/system/health || exit 1

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]