#!/bin/sh
set -e
alembic upgrade head
python scripts/seed_packages.py
exec python -m app.main
