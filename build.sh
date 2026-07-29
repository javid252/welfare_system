#!/usr/bin/env bash
# Render runs this as the build step for the web service.
# See render.yaml -> buildCommand.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate

# Optional: set SEED_DEMO_DATA=true as an env var on the Render service to
# auto-populate demo employees/services/activities and holidays on every
# deploy (safe to re-run — uses get_or_create, so it's a no-op after the
# first successful run). Handy for quickly showing/reviewing the system.
if [ "$SEED_DEMO_DATA" = "true" ]; then
  python manage.py seed_demo_data
  python manage.py seed_holidays
fi
