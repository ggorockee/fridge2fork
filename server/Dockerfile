# Multi-stage build for Fridge2Fork API (uv-based)
# Builder stage
FROM python:3.11-slim-bookworm AS builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv (modern Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files for better caching
COPY requirements.common.txt requirements.prod.txt requirements.dev.txt ./

# Build argument to determine environment-specific dependencies
ARG BUILD_MODE=prod

# Install dependencies using uv (much faster than pip)
RUN if [ "$BUILD_MODE" = "dev" ]; then \
        echo "Installing dev dependencies with uv..."; \
        uv pip install --system -r requirements.dev.txt; \
    else \
        echo "Installing prod dependencies with uv..."; \
        uv pip install --system -r requirements.prod.txt; \
    fi

# Final stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies (including uv for potential runtime package management)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Create non-root user with home directory
RUN useradd --create-home --shell /bin/bash appuser

# Install uv in final stage (for consistent package management)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code (excluding files in .dockerignore)
COPY --chown=appuser:appuser . /app

# Set entrypoint script permissions
RUN chmod +x /app/entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Build arguments for environment configuration
ARG BUILD_MODE=prod

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BUILD_MODE=${BUILD_MODE} \
    APP_ENV=${BUILD_MODE}

# Expose port
EXPOSE 8000

# Add healthcheck for K8s liveness probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/fridge2fork/v1/system/health || exit 1

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]