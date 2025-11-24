#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
max_retries=30
count=0
while ! pg_isready -h postgres -p 5432 -U sentinel_user > /dev/null 2>&1; do
    count=$((count + 1))
    if [ $count -gt $max_retries ]; then
        echo "PostgreSQL did not become ready in time"
        exit 1
    fi
    echo "Waiting for PostgreSQL... ($count/$max_retries)"
    sleep 2
done
echo "✅ PostgreSQL is ready!"

echo "Running database migrations..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    echo "✅ Migrations completed successfully"
else
    echo "❌ alembic.ini not found!"
    exit 1
fi

echo "Creating initial admin user..."
python -c "
from app.services.auth_service import create_initial_admin
try:
    create_initial_admin()
    print('✅ Initial admin user created')
except Exception as e:
    print(f'ℹ️  Admin user setup: {e}')
" || echo "ℹ️  Admin user may already exist"

echo "🚀 Starting Sentinel application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000