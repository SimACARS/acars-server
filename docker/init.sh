#!/bin/sh
set -e

echo "Database init..."
alembic upgrade head

echo "Running tests..."
exec "$@"