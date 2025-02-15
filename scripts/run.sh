#!/bin/bash

# Default values
ENV=${DJANGO_ENV:-development}
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
WORKERS=${WORKERS:-3}

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Export the Django settings module
export DJANGO_SETTINGS_MODULE="core.settings.${ENV}"
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run migrations
echo "Running migrations..."
python src/manage.py migrate

if [ "$ENV" = "development" ]; then
    echo "Starting development server..."
    gunicorn --chdir src \
        --reload \
        --workers 1 \
        --timeout 3600 \
        --bind $HOST:$PORT \
        core.wsgi:application
else
    echo "Starting production server..."
    gunicorn --chdir src \
        --workers $WORKERS \
        --timeout 120 \
        --bind $HOST:$PORT \
        core.wsgi:application
fi 