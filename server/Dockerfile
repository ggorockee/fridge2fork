# Multi-stage build for Python application
# Builder stage
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies in virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim-bookworm

WORKDIR /app

# Create non-root user
RUN useradd --no-create-home appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY . /app

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Add virtual environment to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Copy and set permissions for entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]