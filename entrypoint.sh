#!/bin/sh

# Exit immediately if a command fails
set -e

# Wait for DB to be ready
echo "Waiting for postgres..."
until nc -z db 5432; do
  sleep 1
done
echo "Postgres is up!"

# Run migrations automatically
echo "Running makemigrations and migrate..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files (optional for production)
# python manage.py collectstatic --noinput

# Start the Django server
exec "$@"
