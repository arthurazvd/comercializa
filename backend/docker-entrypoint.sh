#!/bin/sh
set -eu
python manage.py collectstatic --noinput
python manage.py migrate --noinput
if [ "${DEBUG:-False}" = "False" ] || [ -n "${INITIAL_ADMIN_USERNAME:-}" ]; then
  python manage.py bootstrap_admin
fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 2 --timeout 120
