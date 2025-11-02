#!/bin/bash

# Docker entrypoint script for Django application
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h db -p 5432 -U postgres > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL is up and running!"

echo "Waiting for Redis to be ready..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis is up and running!"

# Execute the command passed to the entrypoint
exec "$@"
