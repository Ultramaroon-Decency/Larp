# Multi-stage Dockerfile for FastAPI, PostgreSQL, Redis & Alembic stack

# ── Stage 1: Build dependencies ─────────────────────────────────────────
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# ── Stage 2: Production Runtime ─────────────────────────────────────────
FROM python:3.12-slim

# Create a non-root system user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install runtime utilities (curl, postgresql-client, redis-tools) for health checks and entrypoint scripts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    redis-tools \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application source code, Alembic configs, and entrypoint
COPY . .
RUN chmod +x /app/entrypoint.sh && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# ── Container Health Check ─────────────────────────────────────────────
HEALTHCHECK --interval=15s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
