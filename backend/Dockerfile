FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy alembic configuration
COPY alembic.ini .
COPY alembic ./alembic

# Copy application code
COPY app ./app
COPY init-db.sql .

# Create startup script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 sentinel && \
    chown -R sentinel:sentinel /app && \
    mkdir -p /app/logs && \
    chown -R sentinel:sentinel /app/logs

# Switch to non-root user
USER sentinel

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
ENTRYPOINT ["/app/docker-entrypoint.sh"]