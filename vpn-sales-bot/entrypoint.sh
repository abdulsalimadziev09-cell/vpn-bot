#!/bin/sh
set -e
alembic upgrade head
python scripts/seed_plans.py || true
exec python -m app.main
