#!/bin/sh
# Entrypoint: waits for Postgres, runs migrations, optionally seeds, then starts the API.
set -e

# Wait for Postgres to be ready (compose healthchecks handle this too, but belt-and-braces)
echo "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
for i in $(seq 1 30); do
    if python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('${POSTGRES_HOST}', ${POSTGRES_PORT}))" 2>/dev/null; then
        echo "Postgres is up."
        break
    fi
    sleep 1
done

echo "Running migrations..."
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
    echo "Running seed script..."
    python -m app.seed || echo "Seed failed but continuing."
fi

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WORKERS:-1}"
