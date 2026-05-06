#!/bin/bash

# Exit on error
set -e

echo "Waiting for PostgreSQL..."
until python -c "import os, psycopg2; psycopg2.connect(dbname=os.getenv('POSTGRES_DB','cafit_db'), user=os.getenv('POSTGRES_USER','cafit_user'), password=os.getenv('POSTGRES_PASSWORD',''), host=os.getenv('POSTGRES_HOST','db'), port=os.getenv('POSTGRES_PORT','5432')).close()"; do
	echo "PostgreSQL not ready yet, retrying in 2s..."
	sleep 2
done

echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
