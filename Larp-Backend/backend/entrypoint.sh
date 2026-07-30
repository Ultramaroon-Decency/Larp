#!/bin/bash
set -e

echo "=== Starting AI Research Platform Backend Container (Railway / Docker) ==="

PORT="${PORT:-8000}"

# Run Alembic Database Migrations
echo "Running Alembic database migrations (alembic upgrade head)..."
alembic upgrade head
echo "Alembic migrations completed successfully."

# Start FastAPI application server using Uvicorn app factory on Railway PORT
echo "Starting Uvicorn application server on http://0.0.0.0:${PORT}..."
exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS:-2}"
